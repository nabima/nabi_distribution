# -*- coding: utf-8 -*-

from openerp.osv    import osv,fields
from openerp        import api, models
from datetime       import datetime as dt
from dateutil.parser import parse
from openerp.exceptions import  Warning
import xml.etree.ElementTree as etree

class stock_invoice_onshipping(osv.osv_memory):
    _inherit = "stock.invoice.onshipping"
    def default_get(self,cr,uid,fields_list,context=None):
        if context is None:
            context= {}
        jt = 'sale'
        if context.get('achat',False):
            jt = 'purchase'
        
        if context.get('achat_avoir',False):
            jt = 'purchase_refund'
        
        if context.get('vente_avoir',False):
            jt = 'sale_refund'
        
        if context.get('vente',False):
            jt = 'sale'
        
        if context.get('vente_avoir',False):
            jt = 'sale_refund'
        
        agences = self.pool['res.users'].browse(cr,uid,uid).agence_ids 
        
        j = self.pool['account.journal'].search(cr,uid,[('type','=',jt),('agence_id','in',agences.ids)])
        j = j and j[0] or False
        return {'journal_type': jt ,'journal_id':j}
    
    def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
        
        if context is None:
            context = {}
        domain = {}
        code = False
        if context.get('achat',False):
            jt = 'purchase'
        
        if context.get('achat_avoir',False):
            jt = 'purchase_refund'
        
        if context.get('vente_avoir',False):
            jt = 'sale_refund'
        
        if context.get('vente',False):
            jt = 'sale'
            #code = 'SAJ'
        
        if context.get('vente_avoir',False):
            jt = 'sale_refund'
            #code='SJR'
        
        
        domain['journal_id'] = [('type', '=', jt)]
        if code:
            domain['journal_id'] += [('code','ilike',code)]
        
        agences = self.pool['res.users'].browse(cr,uid,uid).agence_ids
        
        if agences:
            domain['journal_id'] += [('agence_id','in',agences.ids)]
            
        
        return {'domain': domain}
            

class stock_consult_wizard(osv.osv_memory):
    _name='stock.consult.wizard'
    _columns={
    
        'famille':      fields.many2one('product.category',u"Famille d'article"),
        'emplacement':  fields.many2one('stock.warehouse','Emplacement'),
        'fournisseur':  fields.many2one('res.partner','Fournisseur'),
        'article':      fields.many2one('product.product','Fournisseur'),
        'partout':      fields.char('Dans tous les champs'),
        
    }
    
    def appliquer(self,cr,uid,ids, context=None):
        domain=[('location_id.usage','=', 'internal')]
        for o in self.browse(cr,uid,ids):
            if o.famille:
                domain += [('product_id.categ_id','=',o.famille.id)]
            if o.emplacement:
                domain += [('location_id.warehouse_id','=',o.emplacement.id)]
            if o.fournisseur:
                domain += [('product_id.seller_id','=',o.fournisseur.id)]
            if o.article:
                domain += [('product_id','=',o.article.id)]
            if o.partout:
                if len(o.partout) >= 5:
                    domain = ['|','|','|',('product_id.categ_id',   'ilike',o.partout),
                          ('location_id.warehouse_id',           'ilike',o.partout),
                          ('product_id.seller_id',  'ilike',o.partout),
                          ('product_id',            'ilike',o.partout)                        
                        ]
                else:
                    raise Warning('Error',u'il faut saisir au moins 5 caractères dans le champs "Partout"')
        
        
        if domain:
            return {
                'domain': domain or [],
                'name': "Consultation de stock",
                'view_type': 'form',
                'view_mode': 'tree,graph',
                'res_model': 'stock.quant',
                'view_id': False,
               # 'context': "{'journal_id': %d}" % (data['journal_id'],),
                'type': 'ir.actions.act_window'
                 }
        else:
            return {'warning': {'title': 'Error', 'message':'Il faut enseigner au moins un filtre'}}
