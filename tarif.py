# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp import api, models,fields as f
from datetime import datetime,timedelta
from dateutil.parser import parse  
from openerp import tools
from openerp.exceptions import  Warning


class product_tarif_line(osv.osv):
    _name ='product.tarif.line'
    _columns = {
        'parent': fields.many2one('product.tarif','Parent'),
        'product_id':   fields.many2one('product.template','Article',ondelete="restrict"),
        'price':        fields.float('Prix de vente'),
        'reference' :  fields.related('product_id','default_code',  type='char',string ='Réference'),
    }    
    
    
class product_tarif(osv.osv):
    _name="product.tarif"
    _columns = {
    
        'name' :        fields.char('Nom'),
        'active' :      fields.boolean('Actif', default=True),
        'date_start' :  fields.date(u'Date début'),
        'date_end' :    fields.date('Date fin'),
        'line' :        fields.one2many('product.tarif.line', 'parent','Lignes',copy=True),
        'partner_id' :  fields.many2one('res.partner','Client'),
        'partner_ids':    fields.many2many('res.partner','tarif_partner_rel','tarif_id','partner_id','Client'),
        'categ_id':     fields.many2one('res.partner.category',u'Famille client')  ,
        'categ_ids':    fields.many2many('res.partner.category','tarif_categ_rel','tarif_id','categ_id','Famille client'),
        'zone_id':      fields.many2one('res.partner.zone','Zone'),
        'zone_ids':     fields.many2many('res.partner.zone','tarif_zone_rel','tarif_id','zone_id','Zones'),
        'sequence':     fields.integer(u'Séquence'),
        'categ_client': fields.selection([(1,'Particulier'),(2,'Revendeur'),(3,'Promoteur')],u'Catégorie de client'),
    }

    def _get_price(self , cr ,uid, ids, product,client=False, date=False,zone=False,part_categ=False,shipping=False,context=None ):
        pg_mc_obj   = self.pool['product.template.tarif.zone']
        frais_obj   = self.pool['product.frais']
        line_obj    = self.pool['product.tarif.line']
        
        product     = self.pool['product.product'].browse(cr,uid,product).product_tmpl_id
        if not zone:
            zone = client and client.zone or False
        if not part_categ:
            part_categ = client and client.category_id
        if not date:
            date = datetime.now().date()
        else:
            date= parse(date).date()

        selected = []
        prix = []

        domain = ['&','|',('date_start','<',date),('date_start','=',False) , '|',('date_end','>',date),('date_end','=',False)]

        tl_ids = line_obj.search(cr,1,[('product_id','=',product.id)], order="id desc")
        tarif_lines = line_obj.browse(cr,uid,tl_ids)
        for o in tarif_lines:
            if o.parent.date_start and  parse(o.parent.date_start).date() > date:
                continue
            
            if o.parent.date_end and parse(o.parent.date_end).date() < date:
                continue
            
            if not o.parent.active :
                continue
            
            if o.parent.partner_id and o.parent.partner_id.id != client.id:
                continue
            
            if o.parent.categ_ids and not filter(lambda x: part_categ and x.id == part_categ.id or False, o.parent.categ_ids):
                continue
            
            if o.parent.zone_ids and not filter(lambda x: zone and x.id == zone.id or False, o.parent.zone_ids):
                continue
            
            selected += [o.id]

        if not selected :
            if product.seller_id.id == 3223 and product.uom_id.id == 21:
                ctx = {'active_ids':product._ids}
                mc_tarifs = pg_mc_obj.default_get(cr,uid,fields = ['line'], context = ctx)
                if mc_tarifs and 'line' in mc_tarifs:
                    prix = filter(lambda x: x[2]['zone'] == zone and zone.id or False, mc_tarifs['line'])

                    if prix and part_categ.id == 1 :
                        return  ['Tarif non défini: ancien PG, Veuillez contacter le service Tarification !' ,prix[0][2]['tarif_pg']]
                    elif prix:
                        return ['Tarif non défini: ancien PVP, Veuillez contacter le service Tarification !' ,prix[0][2]['tarif_pvp']]
                
            if part_categ.id==1:
                return [u'Tarif non défini: ancien PG, Veuillez contacter le service Tarification !', product.prix_pg]
            else: 
                return [u'Tarif non défini: ancien PVP, Veuillez contacter le service Tarification !', product.prix_pvp]
#            return [u'Tarif non défini: Veuillez contacter le service Tarification !', 0]
        
        else:
            
            price =  line_obj.browse(cr,1, selected).sorted(key=lambda x: (x.parent.sequence,x.id), reverse=True)[0]
            frais = shipping == 'rendu'  and frais_obj._get_frais2(cr,uid,[], prod=product,amount=price.price ,part=client, part_categ = part_categ) or 0
            res_price = frais and price.price + (frais and frais[2] or 0.0) or price.price
            
            return ['%s' % price.parent.name ,res_price]
                
                
                
                
                
class product_tarif_test(models.TransientModel):
    
    _name ="product_tarif_test"
    
    date =      f.Date("date")
    desc =      f.Char("Nom du tarif")
    frais =     f.Float("Mtt. Frais")
    frais_desc= f.Char("desc. Frais")   
    partner =   f.Many2one("res.partner","Client")
    product =   f.Many2one("product.product","Article")
    tarif =     f.Float("Tarif")
    zone =      f.Many2one("res.partner.zone","Zone")
    prod_categ =f.Many2one("product.category",u"Famille d'article")
    part_categ =f.Many2one("res.partner.category","Famille client")
    tarifs=     f.One2many("product.tarif.test.tarif","parent","Tarifs")
    fraiss=      f.One2many("product.tarif.test.frais","parent",u"Frais/Transport")
    shipping=   f.Selection([('rendu','Rendu'),('depart',u'Départ')],string=u"Rendu/Départ",default="depart")
    
    @api.onchange('date','partner','part_categ','product','zone','prod_categ','shipping')
    def onchange_all(self):
        self.tarifs = False
        if self.prod_categ and self.product.categ_id != self.prod_categ:
            self.product = False
        if self.zone and self.partner.zone != self.zone :
            self.partner = False
        if self.part_categ and self.partner.category_id != self.part_categ:
            self.partner = False 
        tarif = self.env['product.tarif']._get_price(product= self.product and self.product.id or False , client = self.partner , date=self.date, zone=self.zone, part_categ = self.part_categ, shipping = self.shipping)
        self.desc= tarif and tarif[0] or False
        self.tarif= tarif and tarif[1] or False
        frais = self.env['product.frais']._get_frais2( prod=self.product , qty=1, amount=1, part=self.partner, part_categ=self.part_categ, zone=self.zone)
        self.frais = frais and frais[2] or False
        self.frais_desc = frais and frais[0] or False
        
        
        
        if  self.product:
            prod_ids = self.env['product.template'].search([('id','=',self.product.product_tmpl_id.id)])
            lines = self.env['product.tarif.line'].search([('product_id','in',prod_ids._ids)])
            vals = []
            #raise Warning("tt","%s" % str(lines._ids))
            fraiss = self.env['product.frais'].search([('x_zones','=',self.zone.id)])
            for l in lines.sorted(key=lambda x:x.parent.sequence,reverse=True):
                vals += [(0,0,{
                    'Tarifs' : l.parent.id,
                    'date_start' : l.parent.date_start,
                    'date_end' : l.parent.date_end,
                    'partner_ids' : l.parent.partner_ids,
                    'categ_ids' : l.parent.categ_ids,
                    'zone_ids' : l.parent.zone_ids,
                    'price' : l.price,
                    'parent': self.id,
                })]
            if vals:
                self.tarifs = vals
                
            vals = []
            for l in fraiss.sorted(key=lambda x: x.sequence,reverse=True):
                vals += [
                (0,0,{
                    'Tarifs' : l.id,
                    'date_start' : l.date_start,
                    'date_end' : l.date_end,
                    
                    'categ_ids' : l.x_part_categ,
                    'zone_ids' : l.x_zones,
                    'price' : l.value,
                    'parent': self.id,
                })
                
                ]
            if vals:    
                self.fraiss = vals
            
            #raise Warning("tt","%s" % self.tarifs)
        
        
        
        # domains
        
        
        
        part_domain = (self.part_categ and [('category_id','=',self.part_categ.id)] or [] ) + (self.zone and [('zone','=',self.zone.id)] or [])
        prod_domain = self.prod_categ and [('categ_id','=',self.prod_categ.id)] or [] 
        return {'domain' : {'partner': part_domain,'product' : prod_domain}}
        
    
class product_tarif_test_tarif(models.TransientModel):
    
    _name ="product.tarif.test.tarif"
    parent      = f.Many2one("product.tarif.test","parent")
    Tarifs      = f.Many2one("product.tarif","Tarif")
    date_start  = f.Date(u'Date début')
    date_end    = f.Date('Date fin')
    partner_ids = f.Many2many('res.partner','tarif_partner_rel','tarif_id','partner_id','Client')
    categ_ids   = f.Many2many('res.partner.category','tarif_categ_rel','tarif_id','categ_id','Famille client')
    zone_ids    = f.Many2many('res.partner.zone','tarif_zone_rel','tarif_id','zone_id','Zones')
    price       = f.Float('Prix de vente')
    
class product_tarif_test_frais(models.TransientModel):
    
    _name ="product.tarif.test.frais"
    parent      = f.Many2one("product.tarif.test","parent")
    Tarifs      = f.Many2one("product.frais","Frais")
    date_start  = f.Date(u'Date début')
    date_end    = f.Date('Date fin')
    partner_ids = f.Many2many('res.partner','tarif_partner_rel','tarif_id','partner_id','Client')
    categ_ids   = f.Many2many('res.partner.category','tarif_categ_rel','tarif_id','categ_id','Famille client')
    zone_ids    = f.Many2many('res.partner.zone','tarif_zone_rel','tarif_id','zone_id','Zones')
    price       = f.Float('Prix de vente')
        
