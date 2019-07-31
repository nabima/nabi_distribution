# -*- coding: utf-8 -*-

from openerp.osv import osv,fields
from openerp.tools.translate import _

class product_supplierinfo(osv.osv):
    _inherit = 'product.supplierinfo'
    _columns = {
        'price_unit' :      fields.float(u'Prix unitaire'),
        'currency_id':      fields.related('name','currency_id',type='many2one',relation='res.currency',string=u'Devise',store=True),
    
    }

class res_partner(osv.osv):
    _inherit="res.partner"    
    _columns = {
        'currency_id':      fields.many2one('res.currency',u'Devise'),
    }
    
class purchase_order(osv.osv):
    _inherit="purchase.order"
    
    def create(self, cr, uid, vals, context=None):
        
        if context.get('importation',False):
            sequence = 'purchase.order.import'
        elif context.get('mg',False):
            sequence = 'purchase.order.mg'
        else:
            sequence = 'purchase.order'
        
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, sequence, context=context) or '/'
        context = dict(context or {}, mail_create_nolog=True)
        order =  super(purchase_order, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [order], body=_("RFQ created"), context=context)
        return order

    
    def onchange_pricelist(self, cr, uid, ids, pricelist_id, context=None):
        res = super(purchase_order,self).onchange_pricelist(cr, uid, ids, pricelist_id)
        ctl_cur = self.browse(cr,uid,ids).partner_id.currency_id.id or False
        if 'value' in res:
            if  ctl_cur:
                res['value']['currency_id'] = ctl_cur
            
        
        return res
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        
        res = super(purchase_order,self).onchange_partner_id( cr, uid, ids, partner_id, context)
        cur =  self.pool['res.partner'].browse(cr,uid,partner_id).currency_id
        
        if cur and 'value' in res:
            if 'pricelist_id' in res['value']:
                
                res['value']['currency_id'] = cur.id or False
        
        return res
    
    def _create_stock_moves(self, cr, uid, order, order_lines, picking_id=False, context=None):
        
        
        
        if context.get('arrivage',False):
            stock_move = self.pool.get('stock.move')
            todo_moves = []
            
            proc_obj = self.pool.get("procurement.group")
            
            new_group = proc_obj.create(cr, uid, {'name': order.name, 'partner_id': order.partner_id.id}, context=context)

            for order_line in order_lines:
                if order_line.state == 'cancel':
                    continue
                if not order_line.product_id:
                    continue

                if order_line.product_id.type in ('product', 'consu'):
                    for vals in self._prepare_order_line_move(cr, uid, order, order_line, picking_id, new_group, context=context):
                        l_moves = stock_move.search(cr,uid,[('purchase_line_id','=',order_line.id),('state','!=','cancel')])
                        l_move_uom_qty = sum( [x.product_uom_qty for x in stock_move.browse(cr,uid,l_moves) ]) or 0.0
                        l_move_uos_qty = sum( [x.product_uos_qty for x in stock_move.browse(cr,uid,l_moves) ]) or 0.0
                        vals['product_uom_qty'] -= l_move_uom_qty 
                        vals['product_uos_qty'] -= l_move_uos_qty
                        
                        if not vals['product_uom_qty']:
                            continue
                        
                        move = stock_move.create(cr, uid, vals, context=context)
                        todo_moves.append(move)

            #todo_moves = stock_move.action_confirm(cr, uid, todo_moves)
            #stock_move.force_assign(cr, uid, todo_moves)
        else:
            super(purchase_order, self)._create_stock_moves( cr, uid, order, order_lines, picking_id, context)
        
        

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    
    def _calc(self,cr,uid,ids,name,arg,context=None):
        res={}
        
        for o in self.browse(cr,uid,ids):
            res[o.id] = {
                    'charge_qty':   0.0,
                    'port_qty':     0.0,
                    'recu_qty':     0.0,
                    'reste_qty':    0.0,
                }
            
            charge_qty = sum([x.product_uom_qty for x in o.move_ids if x.picking_id.date_port == False and x.picking_id.date_chargement != False and x.state == 'assigned' ]) or 0.0
            port_qty =   sum([x.product_uom_qty for x in o.move_ids if x.picking_id.date_port != False       and x.state == 'assigned'   ]) or 0.0
            # Mise à jour : ajouter condition de [x.picking_id.picking_type_id.id != 121]
            recu_qty =   sum([x.product_uom_qty for x in o.move_ids if x.state == 'done' and x.picking_id.picking_type_id.id != 121  ]) or 0.0
            
            res[o.id]['charge_qty'] = charge_qty
            res[o.id]['port_qty']   = port_qty
            res[o.id]['recu_qty']   = recu_qty
            res[o.id]['reste_qty']   = o.product_qty - (recu_qty+charge_qty+port_qty)
    
        return res
    
    def _get_purchase_line(self, cr,uid,ids,context=None):
        res  = []
        for o in self.browse(cr,uid,ids):
            res += [x.purchase_line_id.id for x in o.move_lines] or []
        return res
            
            
    
        
    
    _columns = {
        'currency_id':      fields.related('order_id','currency_id',type='many2one',relation='res.currency',string=u'Devise'),
        
        'charge_qty':       fields.function(_calc, string=u"Qté Chargé" , type="float",multi=True,
                                            store={
                                                'stock.move': (lambda s,c,u,i,ctx=None: [x.purchase_line_id.id for x in s.browse(c,u,i,ctx)] ,['state','date_port','product_uom_qty','date_chargement'],10),
                                                'stock.picking':    (_get_purchase_line, ['state','date_chargement','date_port'], 10),
                                                
                                            }),
        'port_qty':         fields.function(_calc, string=u"Qté port" ,   type="float"  ,multi=True,
                                            store={
                                                'stock.move': (lambda s,c,u,i,ctx=None: [x.purchase_line_id.id for x in s.browse(c,u,i,ctx)] ,['state','date_port','product_uom_qty','date_chargement'],10),
                                                'stock.picking':    (_get_purchase_line, ['state','date_chargement','date_port'], 10),
                                            }),
        'recu_qty':         fields.function(_calc, string=u"Qté recu" ,   type="float"  ,multi=True,
                                            store={
                                                'stock.move': (lambda s,c,u,i,ctx=None: [x.purchase_line_id.id for x in s.browse(c,u,i,ctx)] ,['state','date_port','product_uom_qty','date_chargement'],10),
                                                'stock.picking':    (_get_purchase_line, ['state','date_chargement','date_port'], 10),
                                            }),
        'reste_qty':        fields.function(_calc, string=u"Qté reste" ,  type="float"  ,multi=True,
                                            store={
                                                'stock.move': (lambda s,c,u,i,ctx=None: [x.purchase_line_id.id for x in s.browse(c,u,i,ctx)] ,['state','date_port','product_uom_qty','date_chargement'],10),
                                                'stock.picking':    (_get_purchase_line, ['state','date_chargement','date_port'], 10),
                                            }),
        }      
    
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=False, fiscal_position_id=False, date_planned=False,name=False, price_unit=False, state='draft', context=None):
        rep = super(purchase_order_line,self).onchange_product_id( cr, uid, ids, pricelist_id, product_id, qty, uom_id,partner_id, date_order, fiscal_position_id, date_planned,name, price_unit, state, context)
        product_product = self.pool.get('product.product')                        
        product = product_product.browse(cr, uid, product_id)                                                
        price = price_unit
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                if supplier.price_unit :
                    if  rep['value']['price_unit']:
                        rep['value']['price_unit'] = supplier.price_unit or rep['value']['price_unit']
                    else :
                        rep['value']['price_unit'] = supplier.price_unit or 0.0
                        
        return rep                    
                                
      
      
class purchase_arrivage(osv.osv):
    _name="purchase.arrivage"
    _columns = {
        'state':        fields.selection(selection=[('cancel',u'Annulé'),('draft','Brouillon'),('progress','Encours'),('end',u'Terminé')],string='State',default="draft"),
        'name' :        fields.char(u"No. d'arrivage", default="/"),
        'matricule':    fields.char('Matricule'),
        'date_charge':  fields.date('Date de chargement'),
        'date_arrive':  fields.date(u"Date d'arrivée prévue"),
        'destination':  fields.char(u"Destination"),
        'picking_ids':  fields.one2many('stock.picking','arrivage_id','Arrivages'),

        }
        
    def create(self, cr, uid, vals, context=None):
        
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase_arrivage', context=context) or '/'
        order =  super(purchase_arrivage, self).create(cr, uid, vals, context=context)
        return order
        
        
class stock_picking(osv.osv):
    _inherit="stock.picking"
    _columns = {
        'arrivage_id':  fields.many2one('purchase.arrivage','Arrivage',ondelete="restrict"),
        
        
    
    }
            
        
        
    
    
        
      
      
      
      
      
      
      
      


                
