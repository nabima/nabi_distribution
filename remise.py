# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools import float_compare, float_round
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
from datetime import datetime

from openerp.exceptions import  Warning
import logging
_logger = logging.getLogger(__name__)



class product_remise_line(osv.osv):
    _name = "product.remise.line"
    _columns = {
        'name': fields.many2one('product.remise','Parent'),
        'partner_id': fields.many2one('res.partner','Client'),
        'part_categ_id': fields.many2one('res.partner.category',u'Catég. client'),
        'product_id': fields.many2one('product.product','Article'),
        'prod_categ_id': fields.many2one('product.category',u'Catég. Article'),
        'zone_id': fields.many2one('res.partner.zone','Zone'),
        'company_id': fields.many2one('res.company','Société'),
        'limit': fields.float('Limite'),
        'active': fields.boolean('Active', default=True),
        'limit_ctl':fields.float(u"Nombre de d'application"),
        
        }
        
        
class product_remise(osv.osv):
    _name = "product.remise"
    _columns = {
        'name': fields.char(u"Réference"),
        'active': fields.boolean('Active', default=True),
        'condition': fields.selection(selection=(('partner','Clients'),
                                                ('part_cat',u'Catégorie client'),
                                                ('product','Articles'),
                                                ('prod_cat',u"Famille d'article"),
                                                ('zone','Zone'),
                                               # ('company',u'Société'),
                                                ('all','Tous')
                                        ),
                                    string=u"Condition d'application"),
        'limited': fields.selection(selection=(('qty','Quantité'),('amount','Montant'),('normal','Normal')),string=u"type de limite", default='normal'),
        'limite':fields.integer('Limite'),
        'date_start': fields.date(u"Date de début"),
        'date_end': fields.date(u"Date de fin"),
        'type': fields.selection(selection=(('amount','Montant'),('percent',u'Pourcentage')), string=u"Type de remise"),
        'value': fields.float('Valeur'),
        'line': fields.one2many('product.remise.line','name','Lignes',copy=True),
        'limit_ctl':fields.float(u"Nombre de d'application"),
        
    }
    
    
 
    
    def _get_remise(self, cr, uid, ids, prod=[], qty=False, amount=False, part=[], part_categ=[], zone=[], context=None):
        
        if not zone:
            zone =part and  part.zone and part.zone[0] or []
        
        line_obj = self.pool['product.remise.line']
        date = datetime.now().date()
        domain = ['&','|',('date_start','<=',date), ('date_start','=',False),'|',('date_end','<=',date), ('date_end','=',False)]
        
        remises = self.search(cr,uid,domain, order="id desc")
        remises_all_ids = self.search(cr,uid,['&','|',('condition','=','all'),('condition','=',False)] + domain)
        
        remise_all = remises_all_ids and self.browse(cr,uid,remises_all_ids).sorted(key=lambda x: x.type == 'amount' and x.value  or x.value * amount / 100, reverse=True)[0]
        remise  = []
        if remises:
            ldom = prod != [] and ['|',('product_id','=',prod.id), ('product_id','=',False)] or []
            ldom += part and ['|',('partner_id','=',part.id),('partner_id','=',False)] or []
            ldom += zone and ['|',('zone_id','=',zone.id),('zone_id','=',False)] or []
            ldom += part and ['|',('part_categ_id','in',[x.id for x in part.category_id]),('part_categ_id','=',False)] or []
            ldom += [('name','in',remises)]
            
            line_ids = line_obj.search(cr,uid,ldom, order="id desc")
            lines = line_obj.browse(cr,uid,line_ids).filtered(lambda x: (x.name.limited == 'qty' and (x.limit_ctl + qty) or x.name.limited=='amount' and (x.limit_ctl + amount) or -1) <= x.limit  )
            lines = lines.sorted(key=lambda x: x.name.type == 'amount' and x.name.value  or x.name.value * amount / 100 , reverse=True  )
            
            
            remise = lines and [lines[0].name,lines[0] ,lines[0].name.type == 'amount' and lines[0].name.value  or lines[0].name.value * amount / 100] or []
        
        res = not remise and ( not remise_all and [] or  [remise_all,[],remise_all.type == 'amount' and remise_all.value  or remise_all.value * amount / 100]   ) or  (remise[2] < (remise_all.type == 'amount' and remise_all.value  or remise_all.value * amount / 100) and [remise_all,[],remise_all.type == 'amount' and remise_all.value  or remise_all.value * amount / 100] or remise) 
        
        return res
        
        

class product_frais_line(osv.osv):
    _name = "product.frais.line"
    _columns = {
        'name': fields.many2one('product.frais','Parent'),
        'partner_id': fields.many2one('res.partner','Client'),
        'part_categ_id': fields.many2one('res.partner.category',u'Catég. client'),
        'product_id': fields.many2one('product.product','Article'),
        'prod_categ_id': fields.many2one('product.category',u'Catég. Article'),
        'zone_id': fields.many2one('res.partner.zone','Zone'),
        'company_id': fields.many2one('res.company','Société'),
        'limit': fields.float('Limite'),
        'active': fields.boolean('Active', default=True),
        'limit_ctl':fields.float(u"Nombre de d'application"),
        
        }
        
        
class product_frais(osv.osv):
    _name = "product.frais"
    _columns = {
        'name': fields.char(u"Réference"),
        'active': fields.boolean('Active', default=True),
        'condition': fields.selection(selection=(('partner','Clients'),
                                                ('part_cat',u'Catégorie client'),
                                                ('product','Articles'),
                                                ('prod_cat',u"Famille d'article"),
                                                ('zone','Zone'),
                                               # ('company',u'Société'),
                                                ('all','Tous')
                                        ),
                                    string=u"Condition d'application"),
        'limited': fields.selection(selection=(('qty','Quantité'),('amount','Montant'),('normal','Normal')),string=u"type de limite", default='normal'),
        'limite':fields.integer('Limite'),
        'date_start': fields.date(u"Date de début"),
        'date_end': fields.date(u"Date de fin"),
        'type': fields.selection(selection=(('amount','Montant'),('percent',u'Pourcentage')), string=u"Type de Frais"),
        'value': fields.float('Valeur'),
        'line': fields.one2many('product.frais.line','name','Lignes',copy=True),
        'limit_ctl':fields.float(u"Nombre de d'application"),
        'sequence': fields.integer(u"Séquence"),
        
    }
    
    


        
    def _get_frais(self, cr, uid, ids, prod=[], qty=False, amount=False, part=[], part_categ=[], zone=[], context=None):
        
        if not zone:
            zone = part and part.zone and part.zone[0] or []
        
        line_obj = self.pool['product.frais.line']
        date = datetime.now().date()
        domain = ['&','|',('date_start','<=',date), ('date_start','=',False),'|',('date_end','<=',date), ('date_end','=',False)]
        
        remises = self.search(cr,uid,domain, order="id desc")
        remises_all_ids = self.search(cr,uid,['&','|',('condition','=','all'),('condition','=',False)] + domain)
        
        remise_all = remises_all_ids and self.browse(cr,uid,remises_all_ids).sorted(key=lambda x: x.type == 'amount' and x.value  or x.value * amount / 100, reverse=True)[0] or []
        remise  = []
        
        if remises:
            ldom = [('name','in',remises)]
            ldom += prod != [] and ['|',('product_id','=',prod.id), ('product_id','=',False),'|',('prod_categ_id','=',prod.categ_id.id),('prod_categ_id','=',False)] or []
            ldom += part and ['|',('partner_id','=',part.id),('partner_id','=',False)] or []
            ldom += zone and ['|',('zone_id','=',zone.id),('zone_id','=',False)] or []
            ldom += part and ['|',('part_categ_id','in',[x.id for x in part.category_id]),('part_categ_id','=',False)] or []
            
            
            #raise Warning('ss','%s' % ldom)
            line_ids = line_obj.search(cr,uid,ldom, order="id desc")
            lines = line_obj.browse(cr,uid,line_ids).filtered(lambda x: (x.name.limited == 'qty' and (x.limit_ctl + qty) or x.name.limited=='amount' and (x.limit_ctl + amount) or -1) <= x.limit  )
            lines = lines.sorted(key=lambda x: x.name.type == 'amount' and x.name.value  or x.name.value * amount / 100 , reverse=True  )
            
            
            
            if lines :
                mtt = lines[0].name.type == 'amount' and lines[0].name.value  or lines[0].name.value * amount / 100
                remise = [lines[0].name,lines[0] ,mtt] or []
        
        
        if not remise_all and remise:
            return remise
        elif not remise and remise_all:
            return [ remise_all,[],remise_all.type == 'amount' and remise_all.value  or remise_all.value * amount / 100]
        elif not remise and not remise_all:
            #raise Warning('xxx','%s \n %s' % (remise, remise_all))
            return False
        elif remise[2] < (remise_all.type == 'amount' and remise_all.value  or remise_all.value * amount / 100):
            return [ remise_all,[],remise_all.type == 'amount' and remise_all.value  or remise_all.value * amount / 100]
        else:
            return remise
                
    def _get_frais2(self, cr, uid, ids, prod=[], qty=False, amount=False, part=[], part_categ=[], zone=[], context=None):
        
        zone = zone or (part and part.zone and part.zone[0] or False) or False
        part_categ = part_categ or (part and part.category_id and part.category_id[0] or False) or False
        prod_categ = prod and prod.categ_id.id or False
        
        if not zone:
            pass
        date = datetime.now().date()
        domain = ['&','|',('date_start','<=',date), ('date_start','=',False),'|',('date_end','<=',date), ('date_end','=',False)]
        
        All  = self.search(cr,uid,domain, order="sequence,id desc")
        selected = []
        for o in self.browse(cr,uid,All):
            if o.x_zones and not filter(lambda x: zone and x.id == zone.id or False, o.x_zones):
                continue
            
            if o.x_part_categ and not filter(lambda x: part_categ and  x.id == part_categ.id or False, o.x_part_categ):
                continue
            
            if o.x_prod_categ and not filter(lambda x: prod_categ and x.id == prod_categ or False, o.x_prod_categ):
                #_logger.info('\n ###################  prod categ : %s  #################### \n%s' % (prod_categ,o.x_prod_categ))
                continue
            
            selected += [o.id]
        
        
        


        select  = self.browse(cr,uid,selected) #.filtered(lambda x: (x.limited == 'qty' and (x.limit_ctl + qty) or x.limited=='amount' and (x.limit_ctl + amount) or -1) <= x.limite  )
        sort = select.sorted(key=lambda x: x.sequence    )
            
            
        if sort :
            mtt = sort[0].type == 'amount' and sort[0].value  or sort[0].value * amount / 100
            frais = [sort[0].name,sort[0] ,mtt] or []
            return frais
        return False
    
        
        
        
        

    
    
    
    
    
    
    
