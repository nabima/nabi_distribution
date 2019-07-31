# -*- coding: utf-8 -*-

from openerp.osv import osv,fields
from  datetime import datetime as dt, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import *
from openerp import api, fields as Fields
import logging
from openerp.exceptions import *
#Get the logger
_logger = logging.getLogger(__name__)

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _description = 'Client'
    
    
    def check_client(self,cr,uid,ids,fields, arg,context={}):
        res = {}
        return res
        
        for o in self.browse(cr,uid,ids):
            res[o.id] = False
        
    
    
    def check_client2(self,cr,uid,ids,fields, arg,context={}):
        res={}
        
        
        for o in self.browse(cr,uid,ids):
            
            
            res[o.id] = {
                    'blocked_test':False,
                    'motif_blocage':False,
                     }
            
            # ignorer les le client comptoir et les fournisseur
            if o.id == 1052 or o.customer == False :
                continue

#            # Manque information
#            cin = o.cin or False
#            ice = o.ice or False
#            rc  =  o.rc or False
#            idfiscal  =  o.idfiscal or False

#            if not ((ice and rc and idfiscal) or cin) :
#                res[o.id] = True
#                continue
            
            
            # IMPAYE
            if o.test_impaye:
                impayee = sum([x.amount for x in o.paiement if  x.x_courant !='non' and x.date_impaye != False]) or False
                if impayee :
                    res[o.id] = {
                        'blocked_test':True,
                        'motif_blocage':u"Existance d'impayé",
                         }
                    continue
            
            
            
            # LIMITE DE CREDIT.
            if o.test_limite_credit and o.credit_limit >= 0:
                u" Total des commandes confirmées "
                orders = self.pool['sale.order'].search_read(cr,1,[('partner_id','=',o.id),('shipped','=',False),('invoiced','=',False),('state','not in',('draft','cancel','done'))],['amount_total','picking_ids'])
                
                picking_ids= [x['picking_ids'] for x in orders]
                picking_ids = reduce(lambda x,y:x+y, picking_ids,[])


                livraison_partiel = sum(self.pool['stock.picking'].browse(cr,1,picking_ids).filtered(lambda x:x.state !='cancel').mapped('total_cde')) or 0
                
                
                order_total = sum([x['amount_total'] for x in orders] ) or 0 - livraison_partiel
                
                # Pas de prsie en charge des commandes le 13/12/2018
                # order_total = 0

                u" Total de BL non facturés "
                bls = self.pool['stock.picking'].search_read(cr,1,[('state','=','done'),('invoice_state','!=','invoiced'),'|',('partner_id','=',o.id),('partner_dropship_id','=',o.id)],['total_cde'])
                bls_total = sum([x['total_cde'] for x in bls]) or 0
                
                u" Total des factures Brouillon "
                invoice_draft = self.pool['account.invoice'].search_read(cr,1,[('partner_id','=',o.id),('state','=','draft')],['amount_total'],context=context)
                invoice_draft_total = sum([x['amount_total'] for x in invoice_draft]) or 0
                
                u" Total des réglements non encaissés "
                non_encaissee = sum([x.amount for x in o.paiement if x.x_courant != 'non' and x.date_encaissement == False and x.journal_id.type=='bank']) or 0.0
                
                u" Avances et réglements non lettrés "
                avance = sum([x.writeoff_amount for x in o.paiement if x.x_courant != 'non' and (x.journal_id.type == 'cash' or x.date_encaissement != False) ]) or 0.0
                
                u" limite de crédit + avances > crédit + Cds + Bls + factures brouillon + Reglements non encaissés"
                if   (o.credit_limit + avance - (o.credit + non_encaissee + order_total + bls_total + invoice_draft_total )) <= 1.0 :
                    res[o.id] = {
                        'blocked_test':True,
                         'motif_blocage':u"Dépassement de limite de crédit",
                         }
                    continue

            
            # DATE D'ECHEANCES
            if o.test_echeance:
                date_echeance = dt.now() + relativedelta(days=-60)
                fact_ech = self.pool['account.invoice'].search(cr,1,[('partner_id','=',o.id),'|',('state','=','draft'),('residual','!=',0) ,'|',('date_invoice','<',date_echeance),'&',('date_invoice','=',False),('create_date','<',Fields.Datetime.to_string(date_echeance))])
                bl_ech   = self.pool['stock.picking'].search(cr,1,[('invoice_state','!=','invoiced'),('state','=','done'),'|',('partner_id','=',o.id),('partner_dropship_id','=',o.id) ,'|',('date_done','<',Fields.Datetime.to_string(date_echeance)),'&',('date_done','=',False),('create_date','<',Fields.Datetime.to_string(date_echeance))])
                
                if fact_ech or bl_ech :
                    res[o.id] = {
                         'blocked_test':True,
                         'motif_blocage':u"Au moins une facture ou un BL dépasse 60 jours de délai de réglement",
                         }
                    continue
            
            
            # REGELEMENT NON REMIS AU BANQUE A LA DATE D'ECHEANCE
            if o.test_reglement:
                non_remis = sum([x.amount for x in o.paiement if  x.x_courant !='non' and x.journal_id.type == 'bank' and x.date_remise == False and x.date < Fields.Datetime.to_string(dt.now())]) or False
                if non_remis :
                    res[o.id] = {
                        'blocked_test':True,
                         'motif_blocage':u" Au moins un réglement échu non remis en banque",
                         }
                    continue
            
            
            
            
            # les client Non vérifié seront bloqué pour vente crédit
            if o.verifie==False:
                res[o.id] = {
                        'blocked_test':True,
                        'motif_blocage': u"Ce client n'est pas vérifié!"
                         }
                continue
        return res or False
    
    
    
    _store = {
        'account.voucher':  ( lambda s,c,u,i,x:s.browse(c,u,i,x).partner_id.ids,None,10),
        
        'account.invoice':  ( lambda s,c,u,i,x: [inv.partner_id.id for inv in s.browse(c,u,i,x).filtered(lambda z:z.type in ('out_invoice','out_refund'))],None,10),
        
        'sale.order':       ( lambda s,c,u,i,x:s.browse(c,u,i,x).partner_id.ids,None,10),
        
        'stock.picking':    ( lambda s,c,u,i,x:s.browse(c,u,i,x).partner_id.ids,None,10),
        
        'res.partner':      (lambda s,c,u,i,x:i,None,10),
        
        
            }
    
    
    _columns = { 
        'rc':       fields.char(u'Registre de Commerce',oldname="RC"),
		'idfiscal':       fields.char(u'ID. Fiscal',oldname="IF"),
        'tp':       fields.char(u'Taxe professionnelle',oldname="TP"),
        'ice':      fields.char(u"Identifient Commun d'enreprise",oldname="ICE"),
        'cin':      fields.char(u"Carte d'Identite Nationale",oldname="CIN"),
        'zone':     fields.many2many('res.partner.zone','client_zone_rel','id_client','id_zone', string="Zones"),
        'blocked':  fields.function(check_client, string=u"Bloqué ?", type="boolean"),
        'paiement': fields.one2many('account.voucher','partner_id','Paiement', domain=[('journal_id.type', 'in', ['bank', 'cash']), ('type','=','receipt')]),
        'order_policy': fields.selection([('picking', u'Crédit'),('prepaid', u'Comptant')], u'Type de facturation', required=True,default="picking"),
        'agence' :  fields.many2many('res.agence','res_partner_agence_rel','partner_id','agence_id',string="Agence/client"),
        'picking_ids': fields.one2many('stock.picking','partner_id','Livraisons'),
        'blocked_test':  fields.function(check_client2, string=u"Bloqué2 ?", type="boolean",multi="all",store=_store),
        'motif_blocage': fields.function(check_client2, string="Motif de blocage",type="text",multi="all",store=_store),
        'test_limite_credit':   fields.boolean(u"Blocage sur limite de crédit ",default=True),
        'test_impaye':          fields.boolean(u"Blocage sur impayé ",default=True),
        'test_echeance':          fields.boolean(u"Blocage sur dépassement d''echéance ",default=True),
        'test_reglement':          fields.boolean(u"Blocage sur état de réglements ",default=True),
        'region_stat':  fields.many2one("res.partner.zone",u"Région du client"),
        'verifie':      fields.boolean(u"Ce client est vérifié pour gestion de risque automatique"),
        
        
        }
    
    _sql_constraints = [
        ('unique_rc', 'unique(rc)', u"RC doit être unique!"),
        ('unique_if', 'unique(idfiscal)', u"IF doit être unique!"),
        ('unique_tp', 'unique(tp)', u"TP doit être unique!"),
        ('unique_ice', 'unique(ice)', u"ICE doit être unique!"),
        ('unique_cin', 'unique(cin)', u"CIN doit être unique!"),
        ('unique_name', 'unique(name)', u"Name doit être unique!"),
        ('unique_ref', 'unique(ref)', u"Référence du client doit être unique!"),
    ] 


    

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, [('ref', 'ilike', name)] + args, limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args, limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        return sorted(locations, key=lambda (id, name): ids.index(id))
 
	    
class res_partner_zone(osv.osv):
    _name="res.partner.zone"
    _columns = {
        'name':     fields.char('Name'),
        'marge_pg':     fields.float('Marge PG'),
        'marge_pvp':    fields.float('Marge PVP'),
        }

class res_partner_category(osv.osv):
    _inherit="res.partner.category"
    _columns = {
        'description' : fields.text('Description'),
    }  

class account_voucher(osv.osv):
    _inherit="account.voucher"
    _columns = {
        'date_encaissement' :   fields.date(u"Date d'encaissement"),
        'date_echeance' :       fields.date(u"Date d'écheance"),
        'date_remise' :         fields.date(u"Date de remise"),
        'date_impaye' :         fields.date(u"Date d'impayé"),
        'x_date_reglement' :    fields.date(u'date reglement' ,default=dt.now()),
    }          

class res_agence(osv.osv):
    _name = 'res.agence'    
    _columns = {
        'name': fields.char('agence'),
        #'zone_id': fields.many2one('res.partner.zone', 'Zone'),      
    }

class res_users(osv.osv):
    _inherit = 'res.users'    
    _columns = {
        'agence_ids':       fields.many2many('res.agence','res_users_agence_rel','user_id','agence_id',string=u"Agences autorisées"),        
        'warehouse_ids':    fields.many2many('stock.warehouse','res_users_warehouse_rel','user_id','warehouse_id',string=u"Agences autorisées"),        
    }

class stock_picking(osv.osv):
    _inherit = 'stock.picking'    
    _columns = {
        'matricule':        fields.char(u'Matricule camion'),
        'date_chargement':  fields.date(u'Date de chargement'),
        'date_port':        fields.date(u"Date d'arrivée au port"),
        'bl':               fields.char(u'No. BL'),
    }


        
        
        
        
        
        
        
class sale_order(osv.osv):
    _inherit = "sale.order"
    
    @api.onchange('company_id')
    def nabi_onchange_company(self):
        self.x_zone = self.partner_id.zone and self.partner_id.zone[0] or   self.company_id.x_zone
    
    @api.onchange('x_zone','x_type_livraison')
    def nabi_onchange(self):
        
        for l in self.order_line:
            pass
            
            product_id      = l.product_id.id
            product_uom_qty = l.product_uom_qty
            l_value = l.with_context(zone=self.x_zone.id,shipping=self.x_type_livraison).product_id_change_with_wh(self.pricelist_id.id, 
                                    l.product_id.id, 
                                    l.product_uom_qty,
                                    l.product_uom.id,
                                    l.product_uos_qty,
                                    l.product_uos.id,
                                    l.name,
                                    self.partner_id.id, 
                                    False, False, 
                                    self.date_order, 
                                    l.product_packaging, 
                                    self.fiscal_position.id, True, 
                                    self.warehouse_id.id)
            #raise Warning('s','%s' % str(l_value))
            if 'value' in l_value and 'price_unit' in l_value['value'] :
                l.price_unit        = l_value['value']['price_unit']
                l.tarif             = l_value['value']['price_unit']
                l.product_id        = product_id
                l.product_uom_qty   = product_uom_qty
                if 'product_uom' in l_value['value']:
                    l.product_uom       = l_value['value']['product_uom']
                if 'product_uos' in l_value['value']:
                    l.product_uos       = l_value['value']['product_uos']
                if 'name' in l_value['value']:
                    l.name              = l_value['value']['name']
        
        if  self.order_line: 
            return {'value':{},'warning':{'title':'Attention !','message':u"Les tarifs sur les lignes de commandes vont être adapté en fonction des informations modifié sur l'entête"}}
        
class res_users(osv.osv):
    _inherit =  "res.users"
    discount = Fields.Float(u"Plafond de remise autorisée", default=0)

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    @api.onchange('price_unit')
    def nabi_onchange(self):
        pass
        
        if self.price_unit < self.tarif:
           self.price_unit = self.tarif
           return  {'value':{'price_unit':self.tarif},'warning':{'title':'Attention','message':u"Le prix unitaire ne doit pas être inférieur au tarif de base\n utiliser la colonne remise pour reduire le prix\n"}}

    @api.onchange('discount')
    def onchange_discount(self):
        pass
        #return True
        if not self.discount:
            return {}
        if  self.discount <= self.env['res.users'].sudo().browse(self.env.uid).discount:
            return  {}
        else:
            self.discount = 0
            return {'value':{'discount':0},'warning':{'title':u"Problème d'autorisation",'message':u"Vous n'ếtes autorisé à dépasser le plafond de remise de \n Veuillez contacter Votre résponsable" }}
