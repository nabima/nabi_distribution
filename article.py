# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp import api, models
from datetime import datetime,timedelta
from dateutil.parser import parse  
from openerp import tools
class product_fabriquant(osv.osv):
    _name = 'product.fabriquant'

    

    _columns = {
        'name':fields.char(u'Fabriquant / Marque'),
        'partner':fields.many2one('res.partner',u'Client/fournisseur'),
        
    }
    
class product_gamme(osv.osv):
    _name = 'product.gamme'
    _columns = { 
        'name':fields.char('Gamme'),
        'fabriquant':fields.many2one('product.fabriquant','Fabriquant'),
    }

class product_gamme_commercial(osv.osv):
    _name = 'product.gamme.commercial'
    _columns = { 
        'name':fields.char('Gamme'),
        'famille': fields.many2one('product.category',u"Famille d'article"),
    }
    

    
class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = { 
        'spec':   fields.one2many('product.category.spec','famille',u'Caratctéristiques'),
        'code': fields.char('Code'),
        }
    _sql_constraints = [
        ('name_code', 'unique(code)', u'Code de la famille doit être unique!'),
        ('name_name', 'unique(name)', u'Nom de famille doit être unique!'),
    ]

class product_category_spec(osv.osv):
    _name = 'product.category.spec'
    _columns = { 
        'name':     fields.char(u'Caractéristique',oldname="spec"),
        'famille':  fields.many2one('product.category',u"Famille d'article"),
        'obligatoire': fields.boolean('Obligatoire'),
        
    }
    
class product_spec_value(osv.osv):
    _name = 'product.spec.value'
    _columns = { 
        'name':     fields.char('Valeur'),
        'spec':     fields.many2one('product.category.spec',u"Caractéristique"),
    }    
            
class product_spec(osv.osv):
    _name = 'product.spec'
    
    def spec_name(self,cr,uid,ids,name,arg,context=None):
        
        res = {}
        for o in self.browse(cr,uid,ids):
            res[o.id] =o.value and "%s" % [x.name for x in o.value] or ""
        return res 
    
    _columns = { 
        'spec':         fields.many2one('product.category.spec',u'Caractéristique'),
        'product_id':   fields.many2one('product.template',"Article"),
        'value':        fields.many2many('product.spec.value','product_spec_value_rel','product_id','value_id','Valeur'),
        'obligatoire':  fields.boolean(related="spec.obligatoire",string='Obligatoire'),
        'name':         fields.function(spec_name, string='name',type="char"),
    } 
    
class product_template(osv.osv):
    _inherit = 'product.template'
    
    
    def name_get(self, cr, uid, ids, context=None):
        result = []
        name = super(product_template,self).name_get( cr, uid, ids, context=context)
        for o in self.browse(cr, uid, ids, context):
            result.append((o.id, ('[%s] %s' % (o.default_code or u'*** A CODIFIER ***' , o.name) ) + ( o.active == True and ' ' or u' || INACTIF !')     ))
        return result
    
    def ssearch_read(self,cr,uid, domain=None, fields=None, offset=0,limit=None, order=None,context=None):
        
        if 'readlimitoff' not in context:
            limit = limit < 200 and limit or 200
        res = super(product_template,self).search_read(cr,uid,domain,fields,offset,limit,order,context)
        return res
    
    def new_tarif(self,cr,uid,ids,name,arg,context=None):
        
        res = {}
        for o in self.browse(cr,uid,ids):
            diffdate =o.date_modif and  datetime.now() - parse(o.date_modif ) or False
            res[o.id] = False
            
            if diffdate and diffdate <= timedelta(30):
                res[o.id] =  True
            
        return res 
        
        
    _columns = { 
        'fabriquant':       fields.many2one('product.fabriquant', 'Fabriquant'),
        'pays_origine':     fields.many2one('res.country', u"Pays d'origine"),
        'gamme_produit':    fields.many2one('product.gamme','Gamme de produit'),
        'gamme_commercial': fields.many2one('product.gamme.commercial','Gamme commerciale'),
        'spec':             fields.one2many('product.spec','product_id',u'Caratctéristiques'),
        'prix_pg' :         fields.float('prix PG',track_visibility='always'),
        'prix_pvp' :        fields.float('prix PVP',track_visibility='always'),
        'prix_pr' :         fields.float('prix PR',track_visibility='always'), 
        'prix_devise' :     fields.float('prix Devise',track_visibility='always'), 
        'remarque' :        fields.text('Note',track_visibility='always'),   
        'date_modif' :      fields.datetime(u'Date de modification'),   
        'date_application' :fields.date(u"Date d'application"), 
        'new_tarif' :       fields.function(new_tarif,string='Nouveau tarif OK', type="boolean"),
        'ref_fournisseur':  fields.related('seller_ids','product_code',string='Art. frn.', type="char"),
        'stock':            fields.one2many('product.template.stock','product_tmpl_id',u'Stock par emplacement'),
        'new_code':         fields.char('Nouveau code'),
        'new_name':         fields.char('Nouveau nom'),

    } 
    _sql_constraints = [
        ('unique_name', 'unique(name)', u"Nom de l'article doit être unique!"),
    ]
    
    @api.model
    @api.onchange('prix_pg')
    def onchange_prix_pg(self):
        if self.prix_pg:
          self.date_modif = datetime.now()
    
    @api.onchange('prix_pvp')
    def onchange_prix_pvp(self):
        if self.prix_pvp:
          self.date_modif = datetime.now()
    
    @api.onchange('prix_pr')
    def onchange_prix(self):
        if self.prix_pr:
          self.date_modif = datetime.now()
          
          
    def onchange_categ(self,cr,uid,ids,categ_id,context=None):
        o = self.pool['product.category'].browse(cr,uid,categ_id)
        
        val = [(0,0,{'spec': c.id})  for c in o.spec]
        return {'value':{'spec': val}}
    
    def onchange_spec(self,cr,uid,ids,spec,categ_id,name,context=None):
        c = self.pool['product.category'].browse(cr,uid,categ_id)

        n = name or c.name or ''
        
        if not name:
            
            for s in spec:
                n = "%s %s" % (n, s)
        return True

class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'commission_km' : fields.float(u'Commission kilométrique du trajet'),
    
    }
    _sql_constraints = [
        ('unique_code', 'unique(default_code)', u"Code de l'article doit être unique!"),
        ]
        
    def ssearch_read(self,cr,uid, domain=None, fields=None, offset=0,limit=None, order=None,context=None):
        
        if 'readlimitoff' not in context  :
            limit = limit < 200 and limit or 200
        res = super(product_product,self).search_read(cr,uid,domain,fields,offset,limit,order,context)
        return res
        
class product_template_tarif_zone_line(osv.osv_memory):
    _name = "product.template.tarif.zone.line"        
    _columns = {
        'parent':       fields.many2one('product.template.tarif.zone'),
        'zone' :        fields.many2one('res.partner.zone','Zone'),
        'tarif_pg' :    fields.float('Tarif PG'),
        'tarif_pvp' :   fields.float('Tarif PVP'),
    }
    
class product_template_tarif_zone(osv.osv_memory):
    _name = "product.template.tarif.zone"        
    _columns = {
        'line':fields.one2many('product.template.tarif.zone.line','parent','Tarifs')
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(product_template_tarif_zone, self).default_get(cr, uid, fields, context=context)
        
        z_o   = self.pool['res.partner.zone']
        #z_ids = z_o.search(cr,uid,[])
        z_ids = z_o.search(cr,uid,['|',('marge_pg','!=',0),('marge_pvp','!=',0)])        
        zone = z_o.browse(cr,uid,z_ids)

        record_ids = context and context.get('active_ids', False)
        product = self.pool['product.template'].browse(cr,uid,record_ids)
        vals = []
        if 'line' in fields:
            
            for z in zone:
                
                vals +=  [(0,0,{'zone':       z.id, 
                                'tarif_pg':         product.prix_pg + (z.marge_pg or 0.0),
                                'tarif_pvp':        product.prix_pg + (z.marge_pvp or 0.0),
                               
                                })]
            
            res.update({'line':vals})
        
        return res


class product_template_tarif_achat(osv.osv):
    _name="product.template.tarif.achat"
    _rec_name = 'product_id'
    
    _columns={
        'product_code'  : fields.char('product_code'),
        'product_id'    : fields.many2one('product.template','Product template'),
        'sale_year_qty' : fields.float(u'sale_year_qty'),
        'sale_avg_month': fields.float(u'sale_avg_month'),
        'stock_min'     : fields.float(u'stock_min'),
        'stock_max'     : fields.float(u'stock_max'),
        'company_id'    : fields.many2one('res.company',u'company_id'),
    }

class product_template_stock(osv.osv):
    _name = 'product.template.stock'
    _auto = False
    _columns = {
        'id':               fields.integer('ID'),
        'product_tmpl_id':  fields.many2one('product.template','Article'),
        'location_id':      fields.many2one('stock.location','Emplacement'),
        #'company_id':       fields.many2one('res.company',u'Société'),
        'qty':              fields.float('Stock physique'),
        'reservation':      fields.float(u'Réservation'),
        'categ_id':         fields.char(u'Catégorie'),
        'product_name':     fields.char('Nom article'),
        'location_name':    fields.char('Nom emplacement'),
        'seller_id':        fields.many2one('res.partner',u'Fournisseur'),
        'seller_name':      fields.char(u'Fournisseur'),
        'default_code':     fields.char(u'Code'),
        'stock_min':        fields.float(u'stock Min'),
        'stock_max':        fields.float(u'stock Max'),
        'dispo_phy':        fields.float(u'stock disponible phy.'),
        'dispo_min':        fields.float(u'stock dispo/min'),
        'stock_phy_tot':    fields.float(u'stock phy. group'),
        'qty_in':           fields.float(u'Entrée planifiée'),
        'qty_out':          fields.float(u'Sortie planifiée'),
    }
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'product_template_stock')
        cr.execute("""
            
            CREATE OR REPLACE VIEW product_template_stock AS (
                    
                with sinfo as (
                    select distinct first_value(id ) over(partition by product_tmpl_id) as id from product_supplierinfo
                ),
                
                sinfo1 as (
                    select * from product_supplierinfo inner join sinfo on sinfo.id = product_supplierinfo.id
                ),
                a as (
                    select  pp.product_tmpl_id, 
                            sq.location_id, 
                            
                            sum(sq.qty) as qty,
                            sum(case when sq.reservation_id is null then null
                                when sq.reservation_id  is not null then sq.qty
                                else null 
                                end ) as reservation,
                            pg.name as categ_id,
                            pt.name as product_name,
                            sl.name as location_name,
                            
                            ps.name as seller_id,
                            part.name as seller_name,
                            pp.default_code,
                            sl.agence_id
                            
                            
                                
                    from stock_quant sq
                            inner join stock_location sl on  sl.id = sq.location_id
                            inner join product_product pp on pp.id = sq.product_id 
                            inner join product_template pt on pt.id = pp.product_tmpl_id
                            inner join product_category pg on pt.categ_id = pg.id
                            left outer join sinfo1 ps on ps.product_tmpl_id = pt.id
                            inner join res_partner part on part.id = ps.name
                    where   
                        sl.usage = 'internal' and (pt.state = 'sellable' or pt.state is null) and part.active = true and pp.active = true
                    group by pp.product_tmpl_id, sq.location_id, sl.agence_id,pg.name, pt.name, sl.name,ps.name,part.name,pp.default_code
                    
                        ),
                transfert1 as (
                    select w.id as location , p.product_tmpl_id as product_id, product_qty as qty_out,0 as qty_in
                    from 
                        stock_warehouse w
                                        inner join ordre_transfert t on t.source_id = w.id  
                                        inner join ordre_transfert_line tl on tl.parent = t.id
                                        inner join product_product p on p.id = tl.product_id
                                           
                    where t.state='confirm'
                    union
                    select w.id as location , p.product_tmpl_id as product_id, 0 as qty_out, product_qty as qty_in
                    from 
                        stock_warehouse w
                                        inner join ordre_transfert t on t.destination_id = w.id  
                                        inner join ordre_transfert_line tl on tl.parent = t.id
                                        inner join product_product p on p.id = tl.product_id
                                           
                    where t.state='confirm'
                    
                    
                    
                )    ,
                transfert as (
                
                select location, product_id , sum(qty_out) as qty_out, sum(qty_in) as qty_in from transfert1
                group by location, product_id
                )
                    select row_number() OVER () as id,
                           a.*, sm.stock_min, sm.stock_max,
                           a.qty - coalesce(a.reservation,0)                            - coalesce(tin.qty_out,0) + coalesce(tin.qty_in,0) as dispo_phy,
                           a.qty - coalesce(a.reservation,0) - coalesce(sm.stock_min,0) - coalesce(tin.qty_out,0) + coalesce(tin.qty_in,0) as dispo_min,
                           sum(a.qty) over (partition by a.product_tmpl_id) as stock_phy_tot,
                           tin.qty_in  as qty_in,
                           tin.qty_out as qty_out
                    
                    from a left outer join product_template_tarif_achat sm on  sm.product_id  = a.product_tmpl_id
                                                                           and sm.agence_id  = a.agence_id
                           left outer join stock_location sl on sl.id = a.location_id
                           left outer join transfert tin on tin.product_id   = a.product_tmpl_id and tin.location = sl.warehouse_id
                           
                
                )""")


class product_template_approvisionner(osv.osv_memory):
    _name = "product.template.approvisionner"
    
    _columns = {
        'line' : fields.one2many('product.template.approvisionner.line','parent','disponibilité'),
        'qty'   :   fields.float(u'Qté besoin'),
        'location_id':  fields.many2one('stock.location',u'Dépôt à approvisionner'),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(product_template_approvisionner, self).default_get(cr, uid, fields, context=context)
        vals = []
        if 'line' in fields:
            record_ids = context and context.get('active_ids', False)
            stock   = self.pool['product.template.stock']
            o       = stock.browse(cr,uid,record_ids)

            stock_ids = stock.search(cr,uid,[('dispo_phy','>',0),('id','!=',o[0].id) ,('product_tmpl_id','=',o[0].product_tmpl_id.id)])
            for l in stock.browse(cr,uid,stock_ids):
                vals +=  [(0,0,{'product_tmpl_id':  l.product_tmpl_id.id,
                                'location_id':      l.location_id.id,
                                'agence_id':       l.agence_id.id,
                                'qty':              l.qty,
                                'reservation':      l.reservation,
                                'stock_min':        l.stock_min,
                                'stock_max':        l.stock_max,
                                'dispo_phy':        l.dispo_phy,
                                'dispo_min':        l.dispo_min,
                                
                                })]
            
            res.update({'line':vals, 'qty': -1 * o[0].dispo_min, 'location_id': o[0].location_id.id})
        return res
    
    def create_transfert(self,cr,uid,ids,context=None):
        transfert = self.pool['ordre.transfert']
        transfert_line = self.pool['ordre.transfert.line']
        product = self.pool['product.product']
        
        o = self.browse(cr,1,ids)[0]
        
        record_ids = context and context.get('active_ids', False)
        stock   = self.pool['product.template.stock']
        record       = stock.browse(cr,uid,record_ids)
       
        for l in o.line:
            if l.qty_select:
                print "##################### %s" % record.location_id
                transfert_id = transfert.search(cr,1,[('source_id','=',l.location_id.warehouse_id.id),('destination_id','=',record.location_id.warehouse_id.id),('state','=','draft')]) 
                if not transfert_id:
                    vals= {'source_id':l.location_id.warehouse_id.id,
                            'destination_id':record.location_id.warehouse_id.id,
                        }
                    transfert_id = transfert.create(cr,uid,vals)
                else:
                    transfert_id = transfert_id[0]
                product_id = product.search(cr,uid,[('product_tmpl_id','=',l.product_tmpl_id.id),('active','=',True)])
                tline={
                    'parent':           transfert_id,
                    'origin':           '',
                    'product_id':       product_id[0],
                    'product_qty':      l.qty_select,
                    }
                    
                transfert_line.create(cr,uid,tline)
        
        
        
    
    

class product_template_approvisionner_line(osv.osv_memory):
    _name = "product.template.approvisionner.line"
    _columns = {
        'parent':           fields.many2one('product.template.approvisionner','parent'),
        'product_tmpl_id':  fields.many2one('product.template','Article'),
        'location_id':      fields.many2one('stock.location','Emplacement'),
        'company_id':       fields.many2one('res.company',u'Société'),
        'qty':              fields.float('Stock physique'),
        'reservation':      fields.float(u'Réservation'),
        'stock_min':        fields.float(u'stock Min'),
        'stock_max':        fields.float(u'stock Max'),
        'dispo_phy':        fields.float(u'stock disponible phy.'),
        'dispo_min':        fields.float(u'stock dispo/min'),
        'qty_select':       fields.float(u'Quantité selectionnée'),
    }
    
    
            
                

class product_template_stock_fourn(osv.osv):
    _name = 'product.template.stock.fourn'    
    _auto = False
    _columns = {
        'id':               fields.integer('ID'),
        'product_tmpl_id':  fields.many2one('product.template','Article'),
        'qty':              fields.float('Stock physique'),
        'reservation':      fields.float(u'Réservation'),
        'categ_id':         fields.char(u'Catégorie'),
        'product_name':     fields.char('Nom article'),
        
        'seller_id':      fields.many2one('res.partner',u'Fournisseur'),
        'seller_name':      fields.char(u'Fournisseur'),
        'default_code':     fields.char(u'Code'),
        'stock_min':        fields.float(u'stock Min'),
        'stock_max':        fields.float(u'stock Max'),
        'dispo_phy':        fields.float(u'stock disponible phy.'),
        'dispo_min':        fields.float(u'stock dispo/min'),
        'reste_qty':         fields.float(u'Reste à recevoir'),
        
        
        
    }
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'product_template_stock_fourn')
        cr.execute("""
            
            CREATE OR REPLACE VIEW product_template_stock_fourn AS (   
            
                
                with a as (
                    select product_tmpl_id,
                        sum(qty) as qty,
                        sum(reservation) as reservation,
                        categ_id,
                        product_name,
                        seller_id,
                        seller_name,
                        default_code,
                        sum(stock_min) as stock_min,
                        sum(stock_max) as stock_max,
                        sum(dispo_phy + coalesce(qty_out,0) - coalesce(qty_in,0)) as dispo_phy,
                        sum(dispo_min + coalesce(qty_out,0) - coalesce(qty_in,0)) as dispo_min
                        
                    from product_template_stock
                    group by product_tmpl_id,categ_id,product_name,seller_id,seller_name,default_code)
                , achat as (
                   select p.product_tmpl_id , sum(l.reste_qty) as reste_qty , po.partner_id
                    from purchase_order_line l 
                                inner join product_product p on p.id = l.product_id
                                inner join purchase_order po on po.id = l.order_id
                    where po.shipped <> true
                    group by p.product_tmpl_id  , po.partner_id
                
                )
                
                
                
                select row_number() OVER () as id,
                    a.product_tmpl_id, 
                    a.qty, 
                    a.reservation,
                    a.categ_id,
                    a.product_name,
                    a.seller_id,
                    a.seller_name,
                    a.default_code,
                    a.stock_min,
                    a.stock_max, 
                    a.dispo_phy + coalesce(ach.reste_qty,0) as dispo_phy,
                    a.dispo_min + coalesce(ach.reste_qty,0) as dispo_min  , 
                    ach.reste_qty
                from a
                        left outer join achat ach on ach.partner_id = a.seller_id and ach.product_tmpl_id = a.product_tmpl_id 
            
            
            ) """)
            

class product_template_stock_company(osv.osv):
    _name = 'product.template.stock.company'    
    _auto = False
    _columns = {
        'id':               fields.integer('ID'),
        'product_tmpl_id':  fields.many2one('product.template','Article'),
        #'agence_id':       fields.many2one('res.agence',u'Société'),
        'qty':              fields.float('Stock physique'),
        'reservation':      fields.float(u'Réservation'),
        'categ_id':         fields.char(u'Catégorie'),
        'product_name':     fields.char('Nom article'),
        'default_code':     fields.char(u'Code'),
        'stock_min':        fields.float(u'stock Min'),
        'stock_max':        fields.float(u'stock Max'),
        'dispo_phy':        fields.float(u'stock disponible phy.'),
        'dispo_min':        fields.float(u'stock dispo/min'),
        
    }
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'product_template_stock_company')
        cr.execute("""
            
            CREATE OR REPLACE VIEW product_template_stock_company AS (   
            
                
                with a as (
                    select product_tmpl_id,
                        
                        sum(qty) as qty,
                        sum(reservation) as reservation,
                        categ_id,product_name,default_code,
                        sum(stock_min) as stock_min,
                        sum(stock_max) as stock_max,
                        sum(dispo_phy) as dispo_phy,
                        sum(dispo_min) as dispo_min,
                        agence_id
                        
                    from product_template_stock
                    group by product_tmpl_id,agence_id,categ_id,product_name,default_code)
                select row_number() OVER () as id,* from a
            
            
            ) """)            
            
            
class sale_stats_month(osv.osv):
    _name = 'sale.stats.month'    
    _auto = False
    _columns = {
        'id':               fields.integer('ID'),
        'product_tmpl_id':  fields.many2one('product.template','Article'),
        #'company_id':       fields.many2one('res.company',u'Société'),
        'qty':              fields.float(u'Qté'),
        'categ_id':         fields.many2one('product.category',u'Catégorie'),
        'product_name':     fields.char('Nom article'),
        'default_code':     fields.char(u'Code'),
        'year':             fields.char(u'Année'),
        'month':            fields.char(u'Mois'),
        'seller_id':        fields.many2one('res.partner',u'Fournisseur'),
        
        
        
    }
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sale_stats_month')
        cr.execute("""
            
            CREATE OR REPLACE VIEW sale_stats_month AS (   
            
                
                with a as (
                    select 
                        pp.product_tmpl_id,
                        
                        so.agence_id,
                        coalesce(product_uom_qty,0) as qty,
                        pt.categ_id,
                        pt.name as product_name,
                        pp.default_code,
                        
                        extract(year from date_order) as year,
                        extract(month from date_order) as month
                        
                        
                    from sale_order so 
                                inner join sale_order_line sol on sol.order_id = so.id
                                inner join product_product pp on pp.id = sol.product_id
                                inner join product_template pt on pt.id = pp.product_tmpl_id
                    
                    where so.state != 'cancel' and so.state != 'draft' and  (x_type_vente is null or x_type_vente != 'projet')
                    
                                
                    ),
                    sinfo as (
                    select distinct first_value(id ) over(partition by product_tmpl_id) as id from product_supplierinfo
                ),
                    sinfo1 as (
                    select * from product_supplierinfo inner join sinfo on sinfo.id = product_supplierinfo.id
                ),
                b as (
                
                select
                        product_tmpl_id,
                        
                        
                        sum(qty) as qty,
                        categ_id,
                        product_name,
                        default_code,
                        
                        year,
                        month ,
                        agence_id
                        
                from a
                group by product_tmpl_id,   agence_id,
                        categ_id,
                        product_name,
                        default_code,
                        
                        year,
                        month)
                        
                 
                select row_number() OVER () as id,b.*, ps.name as seller_id
                from b 
                    inner join product_template pt on b.product_tmpl_id = pt.id
                    left outer join sinfo1 ps on ps.product_tmpl_id = pt.id
                
                
            
            
            ) """)            

            
            
            
            
            
            
