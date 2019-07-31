# -*- coding: utf-8 -*-

from openerp.osv    import osv,fields
from openerp        import api, models, fields as Fields
from datetime       import datetime as dt
from dateutil.parser import parse
from openerp.exceptions import  Warning
import xml.etree.ElementTree as etree


class inventaire(osv.osv):
    _name = 'inventaire'
    _description = u"gestion d'inventaire"
    _columns={
    
        'name' :        fields.char(u'N° Inventaire'),
        'sequence':     fields.integer(u'Séquence'),
        'date' :        fields.date(u'date de comptage'),
        'responsable':  fields.many2one('res.users',u'Responsable'),
        'company_id':   fields.many2one('res.company',u'Société'),
        'warehouse_id': fields.many2one('stock.warehouse',u'Entrepôt'),
        'location_id':  fields.many2one('stock.location',u'Emplacement'),
        'state':        fields.selection([('draft','Brouillon'),('progress',u'En cours'),('end',u'fini'),('confirmed',u'Confirmé')],'Etat', default='draft'),
        'stage':        fields.selection([('1e','1er comptage'),('2e',u'2éme comptage'),('3e',u'3éme comptage'),],'Phase',default='1e'),
        'line':         fields.one2many('inventaire.line','parent','Toutes les Lignes',copy=True),
        'line_progress':    fields.one2many('inventaire.line','parent',u'Lignes en couxrs'       ,domain=[('state','in',('progress',))]),
        'line_2e_count':   fields.one2many('inventaire.line','parent',u'Lignes 2éme comptage'  ,domain=[('stage','=','2e'),('state','in',('progress',))]),
        'line_3e_count':   fields.one2many('inventaire.line','parent',u'Lignes 3éme comptage'  ,domain=[('stage','=','3e'),('state','in',('progress',))]),
        'line_confirmed':   fields.one2many('inventaire.line','parent',u'Lignes confirmées'     ,domain=[('state','in',('confirmed','end'))]),
    }
    
     
    
    def stage1(self,cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            for l in o.line:
                if (not l.product_qty1 and l.state == 'draft') :
                    l.state = 'progress'
                    l.stage = '1e'
        return True
    
    def stage2(self,cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            for l in o.line:
                if ((l.product_qty1 and  l.ecart_stock) and l.stage == '1e' ) and l.state=='progress' :
                    l.state = 'progress'
                    l.stage = '2e'
        return True
        
    def stage3(self,cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            for l in o.line:
                if ((l.product_qty2 and  l.ecart_stock) and l.stage == '2e' ) and l.state=='progress':
                    l.state = 'progress'
                    l.stage = '3e'
        return True        
    
    def confirm_line(self,cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            for l in o.line:
                if (l.product_qty1 and not l.ecart_stock) or l.motif :
                    l.state = 'confirmed'
        
        self.stage1(cr,uid,ids,context)
        
        
        return True
        
        
class inventaire_line(osv.osv):
    _name = 'inventaire.line'
    _description = u"gestion d'inventaire  Lignes"
    
    def _calc(self,cr,uid,ids,fields, arg,context=None)    :
        res = {}
        for o in self.browse(cr,uid,ids):
            res[o.id] = {
                    'ecart_comptage'    :False,
                    'ecart_stock'       :False,
                    'ecart_stock_qty'   :False,
                    'product_stk_réel'  :False,
            }
            
            qtes = {'1e': o.product_qty1,
                    '2e': o.product_qty2,
                    '3e': o.product_qty3, 
                    }
            
            qte = qtes[o.stage]        
            
            if o.product_stk != ((o.product_qty1 or 0.0) + (o.product_rebut   or 0.0)):
                res[o.id]['ecart_stock']=True
            
            res[o.id]['ecart_stock_qty'] =  o.product_stk - (o.product_qty1 or 0.0) - (o.product_rebut   or 0.0)         
                
            
            
            if o.state == 'confirmed':
                res[o.id]['product_stk_réel'] = qte
                
            
            
            
            return res
    
    
    _columns={
        'parent' :          fields.many2one('inventaire',u'Inventaire'),
        'product_id':       fields.many2one('product.product',u'Article'),
        'product_uom':      fields.related('product_id','uom_id',string=u'Unité',type="many2one", relation="product.uom"),
        'categ_id':         fields.related('product_id','categ_id',string=u'Famille',type="many2one", relation="product.category"),
        'seller_id':        fields.related('product_id','seller_id',string=u'Fournisseur',type="many2one", relation="res.partner"),
        'product_stk':      fields.float(u'Stock théorique'),
        'product_qty1':     fields.float(u'Quantité 1', default=False),
        'product_qty2':     fields.float(u'Quantité 2', default=False),
        'product_qty3':     fields.float(u'Quantité 3', default=False),
        'product_rebut':    fields.float(u'Casse/Rebut', default=False),
        'ecart_comptage':   fields.function(_calc,multi="calc", store=True,type='boolean',string=u'Ecart de comptage'),
        'ecart_stock':      fields.function(_calc,multi="calc", store=True,type='boolean',string=u'Ecart de stock'),
        'ecart_stock_qty':  fields.function(_calc,multi="calc", store=True,type='float'  ,string=u'Qté Ecart de stock'),
        'product_stk_reel': fields.function(_calc,multi="calc", store=True,type='float'  ,string=u'Stock réel après validation'),
        'motif':            fields.text(u"Motif de l'écart"),
        'state':            fields.selection([('draft','Brouillon'),('progress',u'En cours'),('end',u'fini'),('confirmed',u'Confirmé')],'Etat', default='draft'),
        'stage':            fields.selection([('1e','1er comptage'),('2e',u'2éme comptage'),('3e',u'3éme comptage'),],'Phase',default='1e'),
    }
           
    
    
class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    #_get_price(self , cr ,uid, ids, product,client=False, date=False,zone=False,part_categ=False,shipping=False,context=None )
    
    def _total_cde(self,cr,uid,ids,fields, arg,context=None):
        res = {}
        tarif = self.pool['product.tarif']
        for o in self.browse(cr,uid,ids):
            if o.partner_id.id == 1052:
                res[o.id] = False
                continue
            tt = 0.0
            for l in o.move_lines:
                price_unit = False
                
                sale        = o.sale_id or o.order_dropship_id or False
                order_line  = sale and sale.order_line and  sale.order_line.filtered(lambda x: x.product_id.id == l.product_id.id ) or False
                    
                if order_line:
                    price_unit = order_line[0].price_unit
                elif sale and (price_unit == False or price_unit == 0.0):
                    price_unit = tarif._get_price(cr,1,[],
                                                    product = l.product_id.id,
                                                    client  = sale.partner_id  or o.partner_id, 
                                                    zone    = sale.x_zone or False,
                                                    shipping= sale.x_type_livraison or False,
                                                    context = context)
                    price_unit = price_unit and price_unit[1] or False
                else:
                    price_unit = l.price_unit
                tt += round(price_unit * l.product_qty,2) # Enlever la multiplication de 20%
            
            res[o.id] = tt or False
        return res 
    
    def _get_sale_order(self,cr,uid,ids,context=None):
        return []
        res = []
        res = self.pool['stock.picking'].search(cr,uid,['|',('sale_id','in',ids),('order_dropship_id','in',ids)])
        return res
            
    def _get_stock_move(self,cr,uid,ids,context=None):
        res = []        
        for o in self.browse(cr,uid,ids):
            res += o.picking_id.ids if o.picking_id else []
        return res
    
    def _get_sale_order_line(self,cr,uid,ids,context=None):
        return []
        res = []
        order_ids = [ x['order_id'] for x in self.read(cr,uid,ids,['order_id'])]
        res = self.pool['stock.picking'].search(cr,uid,['|',('sale_id','in',order_ids),('order_dropship_id','in',order_ids)])
        return res
        
        
#    def _get_invoice(self,cr,uid,ids,context=None):
#        #return []
#        pids =[]
#        pnames=[]
#        for o in self.browse(cr,1,ids):
#            pnames += [x.origin for x in o.invoice_line]
#        res = self.pool['stock.picking'].search(cr,1,[('name','in',pnames)])
            
                
            
        return res
        
    
    
    
    _TOTAL_CDE_STORE = {
        'stock.picking':    (lambda s,c,u,i,x:i,[],10),
        'stock.move':       (_get_stock_move,['product_id','price_unit','product_qty'],10),
        'sale.order':       (_get_sale_order,['partner_id','x_zone','x_type_livraison'],10),
        'sale.order.line':  (_get_sale_order_line,['product_id','price_unit'],10),
        }
    
    
    
    def _get_invoice_store(self,cr,uid,ids,context=None):
        res = []
        pnames = []
        for o in self.browse(cr,1,ids):
            pnames += [x.origin for x in o.invoice_line]
        res = pnames and self.pool['stock.picking'].search(cr,1,[('name','in',pnames)]) or []
        return res
        
    _PRC_STORE = {
        'stock.picking':        (lambda s,c,u,i,x:i,[],10),
        'account.invoice': (_get_invoice_store,['invoice_line','state'],10),
        }
        
    
    def get_sale_info(self,cr,uid,ids,fields, arg,context=None):
    
        pass
        res = {}
        for o in self.browse(cr,uid,ids,context=context):
            
            
            client_cde            = o.sale_id and o.sale_id.client or False
            client_ref            = o.sale_id and o.sale_id.client_order_ref  or False
            partner_dropship_id   = [x.purchase_line_id.order_id.dest_address_id.id       for x in o.move_lines if x.purchase_line_id and x.purchase_line_id.order_id and x.purchase_line_id.order_id.dest_address_id   or False  ]
            partner_dropship_name = [x.purchase_line_id.order_id.dropship_order_id.client for x in o.move_lines if x.purchase_line_id and x.purchase_line_id.order_id and x.purchase_line_id.order_id.dropship_order_id or False  ]
            order_dropship_id     = [x.purchase_line_id.order_id.dropship_order_id.id     for x in o.move_lines if x.purchase_line_id and x.purchase_line_id.order_id and x.purchase_line_id.order_id.dropship_order_id or False  ]
            
            res[o.id] = {
                'client_cde':client_cde,
                'client_ref':client_ref,
                'partner_dropship_id':  partner_dropship_id     and partner_dropship_id[0]      or False,
                'partner_dropship_name':partner_dropship_name   and partner_dropship_name[0]    or False,
                'order_dropship_id':    order_dropship_id       and order_dropship_id[0]        or False,
            }
        return res
        
    def _prc_invoiced(self,cr,uid,ids,fields,arg,context=None):
        res = {}
        invo = self.pool['account.invoice.line']
        for o in self.browse(cr,uid,ids,context=context):
            res[o.id] = {
                'invoices': [],
                'prc_inv_sale'      :False,
                'prc_inv_purchase'  :False,
            }
            
            invoices =[]
            
            if 'invoices' in fields:
                invoices = invo.search(cr,uid,[('origin','=',o.name),('invoice_id.state','!=','cancel')])
                res[o.id]['invoices'] = invoices
            
            if 'prc_inv_purchase' in fields:
                if not invoices:
                    invoices = invo.search(cr,uid,[('origin','=',o.name)])
                prc_inv_purchase= sum(invo.browse(cr,1,invoices).mapped(lambda x: x.invoice_id.type == 'in_invoice' and x.price_subtotal or x.invoice_id.type == 'in_refund' and - x.price_subtotal or 0))
                res[o.id]['prc_inv_purchase'] = o.total_cde and abs(100 * prc_inv_purchase /o.total_cde)  or prc_inv_purchase and  100 or 0
            
            
            if 'prc_inv_sale' in fields:
                if not invoices:
                    invoices = invo.search(cr,uid,[('origin','=',o.name)])
                prc_inv_sale    = sum(invo.browse(cr,1,invoices).mapped(lambda x: x.invoice_id.type == 'out_invoice' and x.price_subtotal or x.invoice_id.type == 'out_refund' and - x.price_subtotal or 0))
                res[o.id]['prc_inv_sale']     =  o.total_cde and   abs(100 *  prc_inv_sale / (o.total_cde or 1)) or prc_inv_sale and 100 or 0
    
        return  res


            
            
    _columns = {
        'stock_picking_type_code':  fields.related('picking_type_id', 'code', string="Picking Type", type="char", readonly="True",store=True),
        'total_cde':                fields.function(_total_cde,    string="Total TTC" ,         type="float",store=_TOTAL_CDE_STORE),
        'client_cde':               fields.function(get_sale_info, string="Client dest." ,      type="char", store=True, multi="all"),
        'client_ref':               fields.function(get_sale_info, string="Ref." ,              type="char", store=True, multi="all"),        
        'partner_dropship_name':    fields.function(get_sale_info, string="Nom du client",      type="char", store=True, multi="all"),
        'partner_dropship_id':      fields.function(get_sale_info, string="Client dropship",    type="many2one", relation="res.partner",    store=True, multi="all"),
        'order_dropship_id':        fields.function(get_sale_info, string="Cde. vente ",        type="many2one", relation="sale.order",     store=True, multi="all"),
        'invoices':                 fields.function(_prc_invoiced,relation = 'account.invoice.line',string=u'Factures', type="many2many",multi="prc", 
#                                    store = {'account.invoice':(_get_invoice,None,10),}
                                    ),
        'invoiced_sale':            fields.boolean(u"Facturé en ventes"),
        'invoiced_purchase':        fields.boolean(u"Facturé en achats"),
        'prc_inv_sale':             fields.function(_prc_invoiced,string=u"Pourcentage de facturation ventes", type="float", multi="prc",store=_PRC_STORE),
        'prc_inv_purchase':         fields.function(_prc_invoiced,string=u"Pourcentage de facturation achats", type="float", multi="prc",store=_PRC_STORE),
    }


    _defaults = {
        'invoice_state': lambda *args, **argv: '2binvoiced'
    }
    
    def write(self,cr,uid,ids,vals,context=None):
        pto = self.pool['stock.picking.type']
        pt = False
        if 'picking_type_id' in vals:
        
            pt = pto.browse(cr,uid,vals['picking_type_id'])
            if pt.warehouse_id:
                company_id = pt.warehouse_id.company_id.id
                vals['company_id'] = company_id or vals['company_id']
                location_src_id     = pt.default_location_src_id.id
                location_dest_id    = pt.default_location_dest_id.id
                p = self.browse(cr,uid,ids,context)
                m = self.pool['stock.move']
                for l in p.move_lines:
                    l.company_id        = company_id
                    l.picking_type_id   = pt.id
                    l.location_id       = location_src_id or l.location_id
                    l.location_dest_id  = location_dest_id or l.location_dest_id
                    
                        
        
            
        res = super(stock_picking,self).write(cr,uid,ids,vals,context)
        return res
    
    def create(self,cr,uid,vals,context=None):
        res = super(stock_picking,self).create(cr,uid,vals,context)
        if 'picking_type_id' in vals:
            self.write(cr,uid,res,{'picking_type_id':vals['picking_type_id']})
            
        return res
    
    
    def creer_facture_automatique(self, cr, uid, ids, agence, context=None):
        journal_type = 'sale'
        ctx = {}
        journal2type = {'sale':'out_invoice', 'purchase':'in_invoice', 'sale_refund':'out_refund', 'purchase_refund':'in_refund'}
        ctx['date_inv'] = Fields.Date.today()
        acc_journal = self.pool.get("account.journal")
        
        inv_type =  journal2type.get(journal_type) or 'out_invoice'
        journal_id = acc_journal.search(cr,uid,[('agence_id','=', agence.id ),('type','=',journal_type)])
        journal_id = journal_id and journal_id[0] or False
        
        if not journal_id:
            raise Warning("Journal Error",u"Aucun journal défini pour l'agence en cours")
        
        
        ctx['inv_type'] = inv_type

        res = self.action_invoice_create(cr, uid, ids,
              journal_id = journal_id,
              group = False,
              type = inv_type,
              context=ctx)
        return res

    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        res = super(stock_picking,self).do_transfer(cr,uid,picking_ids,context=context)
        pt121 = self.pool['stock.picking.type'].browse(cr,uid,121)
        if res:
            for picking in self.browse(cr, uid, picking_ids, context=context):

                if picking.picking_type_id.id == 6 and picking.partner_dropship_id.id  :
                    cp = self.copy(cr, uid, picking.id, {
                    'name'                      : '/',
                    'agence_id'                 : picking.order_dropship_id.id and picking.order_dropship_id.agence_id.id or picking.agence_id.id,
                    #'pack_operation_ids'        : [],
                    'backorder_id'              : picking.id,
                    'origin'                    : '%s, %s' % (picking.origin ,picking.name),
                    'picking_type_id'           : 121,
                    'partner_id'                : picking.partner_dropship_id.id,
                    'invoice_state'             :'2binvoiced',
                    'picking_type_code'         :'outgoing',
                    'location_id'               : pt121.default_location_src_id.id,
                    'location_dest_id'          : pt121.default_location_dest_id.id,
                    'sale_id'                   : picking.order_dropship_id.id,
                    'date_done'                 : dt.now(),
                         })
                    cpo = self.browse(cr,uid,cp)
                    cpo.move_lines.mapped(lambda x:x.write({ 'location_id'     : pt121.default_location_src_id.id,
                                                             'location_dest_id': pt121.default_location_dest_id.id,}))
                    cpo.pack_operation_ids.mapped(lambda x:x.write({ 'location_id'     : pt121.default_location_src_id.id,
                                                                     'location_dest_id': pt121.default_location_dest_id.id,}))
                    cpo.action_confirm()
                    cpo.action_assign()
                    cpo.do_transfer()
                elif picking.picking_type_id.id == 6 and not picking.partner_dropship_id.id  :
                    raise osv.except_osv(u"Procédure livraison directe non respectée !",u" Le champs (Commande de ventes) est obligatoire !\n Impossible de transferer les bons de réception sur livraison directe qui ne contient pas la commande de vente liée !")
        ### Facturation automatique des facture
                if uid ==1 :
                    self.sudo().creer_facture_automatique(cr,uid,picking.ids,picking.agence_id,context=context)
        
        ### facturation
        
        return res
            
                

class stock_quant(osv.osv):
    _inherit = 'stock.quant'
    
    def create(self,cr,uid,vals, context=None):
                
        res = super(stock_quant,self).create(cr,uid,vals,context)           
        if 'location_id' in vals:
            l = self.pool['stock.location'].browse(cr,uid,vals['location_id'])
            company = l.company_id.id or False
            self.write(cr,uid,res,company and {'company_id':company} or {})
        return res
        
        
        
class stock_move(osv.osv):

    _inherit = "stock.move"
    
    def _calc_all(self,cr,uid,ids,fields, arg,context=None)    :
        res = {}
        
        for o in self.browse(cr,1,ids):
            res[o.id] = {
                    'qty_signe'    :False,
            }
            continue
            #function suspendu : à revoir completement
            
            if o.state != 'done':
                continue
            qty_signe = False
            if o.location_id.usage == 'internal' and o.location_dest_id.usage != 'internal'  :
                qty_signe = -1 * o.product_qty
            elif o.location_dest_id.usage == 'internal' and o.location_id.usage != 'internal':
                qty_signe =  o.product_qty
            res[o.id]['qty_signe'] = qty_signe
        return res
    
    _columns = {
        'qty_signe' :  fields.function(_calc_all, string=u'Qté mvt', type="float",multi="calc", store=True ),
    }
    
    ###################################
    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        fp_obj = self.pool.get('account.fiscal.position')
        # Get account_id
        fp = fp_obj.browse(cr, uid, context.get('fp_id')) if context.get('fp_id') else False
        name = False
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = move.product_id.property_account_income.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_income_categ.id
            if move.procurement_id and move.procurement_id.sale_line_id:
                name = move.procurement_id.sale_line_id.name
        else:
            account_id = move.product_id.property_account_expense.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_expense_categ.id
        fiscal_position = fp or partner.property_account_position
        account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)

        # set UoS if it's a sale and the picking doesn't have one
        uos_id = move.product_uom.id
        picking_code = move.picking_id and move.picking_id.picking_type_id.id or False
        if context.get('vente',False) == True and context.get('vente_avoir',False) == False and move.picking_id  and inv_type in ('out_invoice', 'out_refund') and (move.picking_id.picking_type_id.code == 'incoming'  or move.picking_id.picking_type_id.default_location_src_id.usage=='customer') :
            quantity = - (move.product_uom_qty)
            if move.picking_id.picking_type_id.id == 6 and move.picking_id.picking_type_id.code == 'incoming' and dt.strptime(move.picking_id.date,'%Y-%m-%d %H:%M:%S') <= dt.strptime("2019-04-25 17:30", '%Y-%m-%d %H:%M'):
                quantity =  (move.product_uom_qty)
            
        else:
            quantity = move.product_uom_qty
        #if move.product_uos:
        #    uos_id = move.product_uos.id
        #    quantity = move.product_uos_qty

        taxes_ids = self._get_taxes(cr, uid, move, context=context)
        
        res =  {
            'name': name or move.name,
            'account_id': account_id,
            'product_id': move.product_id.id,
            'uos_id': uos_id,
            'quantity': quantity,
            'price_unit': self._get_price_unit_invoice(cr, uid, move, inv_type,context=context),
            'invoice_line_tax_id': [(6, 0, taxes_ids)],
            'discount': 0.0,
            'account_analytic_id': False,
            'x_move_id':move.id,
            'x_bl':move.picking_id.id,
        }
        
        if context.get('vente',False) == True and move.picking_id.order_dropship_id : 
            return res
            raise Warning('','%s' % str( [x.price_unit for x in  move.picking_id.order_dropship_id.order_line if x.product_id.id == move.product_id.id]))
        return res

    
    #################################


class purchase_order(osv.osv):
    _inherit="purchase.order"
    _columns={
        'dropship_order_id' : fields.many2one('sale.order','Commande dropship')
    }


class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'

    def default_get(self, cr, uid, fields, context=None):
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        if pick:
            if 'invoice_state' in fields:
                if pick.invoice_state=='invoiced' or (pick.partner_id and pick.partner_id.id == 1052 or False) or (pick.partner_dropship_id and pick.partner_dropship_id.id == 1052 or False ):
                    res.update({'invoice_state': '2binvoiced'})
                else:
                    res.update({'invoice_state': 'none'})
        return res
        
        
    def _create_returns(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('stock.return.picking.line')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        returned_lines = 0

        # Cancel assignment of existing chained assigned moves
        moves_to_unreserve = []
        for move in pick.move_lines:
            to_check_moves = [move.move_dest_id] if move.move_dest_id.id else []
            while to_check_moves:
                current_move = to_check_moves.pop()
                if current_move.state not in ('done', 'cancel') and current_move.reserved_quant_ids:
                    moves_to_unreserve.append(current_move.id)
                split_move_ids = move_obj.search(cr, uid, [('split_from', '=', current_move.id)], context=context)
                if split_move_ids:
                    to_check_moves += move_obj.browse(cr, uid, split_move_ids, context=context)

        if moves_to_unreserve:
            move_obj.do_unreserve(cr, uid, moves_to_unreserve, context=context)
            #break the link between moves in order to be able to fix them later if needed
            move_obj.write(cr, uid, moves_to_unreserve, {'move_orig_ids': False}, context=context)

        #Create new picking for returned products
        pick_type_id = pick.picking_type_id.return_picking_type_id and pick.picking_type_id.return_picking_type_id.id or pick.picking_type_id.id
        
        ####### TODO: changer le type d'opération de retour pour les livraison direct avant 25/02/19; suite à un changement dans la procédure de dropship 
        if pick.picking_type_id.id == 6 and dt.strptime(pick.date,'%Y-%m-%d %H:%M:%S') <= dt.strptime("2019-04-25 17:30", '%Y-%m-%d %H:%M'):
            pick_type_id = 104
        
        invoice_state = data['invoice_state']   
        
        ####### fin modification
        new_picking = pick_obj.copy(cr, uid, pick.id, {
            'move_lines': [],
            'picking_type_id': pick_type_id,
            'state': 'draft',
            'origin': pick.name,
        }, context=context)

        for data_get in data_obj.browse(cr, uid, data['product_return_moves'], context=context):
            move = data_get.move_id
            if not move:
                raise osv.except_osv(_('Warning !'), _("You have manually created product lines, please delete them to proceed"))
            new_qty = data_get.quantity
            if new_qty:
                # The return of a return should be linked with the original's destination move if it was not cancelled
                if move.origin_returned_move_id.move_dest_id.id and move.origin_returned_move_id.move_dest_id.state != 'cancel':
                    move_dest_id = move.origin_returned_move_id.move_dest_id.id
                else:
                    move_dest_id = False

                returned_lines += 1
                move_obj.copy(cr, uid, move.id, {
                    'product_id': data_get.product_id.id,
                    'product_uom_qty': new_qty,
                    'product_uos_qty': new_qty * move.product_uos_qty / move.product_uom_qty,
                    'picking_id': new_picking,
                    'state': 'draft',
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': move.location_id.id,
                    'picking_type_id': pick_type_id,
                    'warehouse_id': pick.picking_type_id.warehouse_id.id,
                    'origin_returned_move_id': move.id,
                    'procure_method': 'make_to_stock',
                    'restrict_lot_id': data_get.lot_id.id,
                    'move_dest_id': move_dest_id,
                    'invoice_state':invoice_state

                })

        if not returned_lines:
            raise osv.except_osv(_('Warning!'), _("Please specify at least one non-zero quantity."))

        pick_obj.action_confirm(cr, uid, [new_picking], context=context)
        pick_obj.action_assign(cr, uid, [new_picking], context)
        
        

        return new_picking, pick_type_id
    

class stock_inventory(osv.osv):
    _inherit="stock.inventory"
    
    state = Fields.Selection(selection=[('draft','Draft'),('cancel','Cancelled'),('confirm','In Progress'),('validation','Encours de validation'),('done','Validated')])
        
        
        
        

        
        
        
        
        
