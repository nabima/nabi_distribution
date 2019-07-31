# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp import api, models
from datetime import datetime,timedelta
from dateutil.parser import parse  
from openerp import tools, fields as Fields,api
from openerp.exceptions import *
#Get the logger
import logging
_logger = logging.getLogger(__name__)

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}

class sale_affaire(osv.osv):
    _name = 'sale.affaire'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _track = {
        'state': {
            'nabi_distribution.mt_affaire_open':  lambda self, cr, uid, obj, ctx=None: obj.state in ['open', 'progress'],
            'nabi_distribution.mt_order_end':     lambda self, cr, uid, obj, ctx=None: obj.state in ['close','posted']
        },
    }
    _columns = { 
        'name': fields.char(u'Dossier/Affaire',default='/'),
        'description':     fields.char('Description'),
        'client':   fields.char('Nom Client'),
        'categ_id': fields.many2one('res.partner.category','Type'),
        'is_company':fields.boolean(u'Société'),
        'adresse':  fields.text('Adresse client'),
        'state':    fields.selection(string='Etat', selection=[('open','Ouvert'),('close',u'Terminé'),('posted',u'Facturé')]),
        'saleorder_ids':    fields.one2many('sale.order','affaire','Commandes'),
        'invoice_ids':      fields.one2many('account.invoice','affaire','Facture'),
        'picking_ids':      fields.one2many('stock.picking','affaire','Livraisons'),
        'payment_ids':      fields.one2many('account.voucher','affaire','Payment'),
        'date_limit':       fields.date(u'Date validité',track_visibility='always'),
        'plafond_credit':   fields.float(u'Plafond de crédit', track_visibility='always'),
        
    }
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, 1, 'sale.affaire', context=context) or '///'
        context = dict(context or {}, mail_create_nolog=True)
        affaire =  super(sale_affaire, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [affaire], body=u"Affaire créée !", context=context)
        return affaire

class sale_order(osv.osv):
    _inherit="sale.order"

    _STATES={
        'draft':    [('readonly',False)],
        'sent':     [('readonly',False)],
        'cancel':   [('readonly',True)],
        'waiting_date':[('readonly',True)],
        'progress':[('readonly',True)],
        'manual':[('readonly',True)],
        'shipping_except':[('readonly',True)],
        'invoice_except':[('readonly',True)],
        'done':         [('readonly',True)],
    }

    _columns = {
        'affaire' : fields.many2one('sale.affaire','Affaire', ondelete="restrict",states=_STATES),
        'client' : fields.char('Nom Client',states=_STATES),
        'adresse' : fields.text('Adresse client',states=_STATES),
        'cat_client':   fields.many2one("res.partner.category",u"Catégorie de client",states=_STATES),
    }

    def get_states(self):
        return {'invisible' : True}

    company_id          = Fields.Many2one(states=_STATES)
    client_order_ref    = Fields.Char(states=_STATES)
    warehouse_id        = Fields.Many2one(states=_STATES)
    fiscal_position     = Fields.Many2one(states=_STATES)
    user_id             = Fields.Many2one(states=_STATES)
    dropship            = Fields.Boolean("Livraison directe client",states=_STATES)
    dropship_partner_id = Fields.Many2one('res.partner','Fournisseur',states=_STATES)
    type_livraison      = Fields.Selection(selection=[('depart','Départ'),('rendu','Rendu')],string='Type de livraison', states=_STATES)
    zone                = Fields.Many2one("res.partner.zone","Zone de livraison",states=_STATES)
    order_line          = Fields.One2many(states=_STATES)


    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(sale_order,self).fields_view_get(cr, user, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
        
        if ('delete_manual' in context):
            if 'fields' in res and 'order_policy' in res['fields']: 
                
                ss = res['fields']['order_policy']['selection']
                ss.remove(ss[0])
                res['fields']['order_policy']['selection'] = ss

        return res



    def _prepare_invoice(self, cr, uid, order,lines, context=None): 
        res = super(sale_order,self)._prepare_invoice(cr, uid, order,lines,  context=context)
        if order.affaire:
            res.update({'affaire':order.affaire.id, 
                        'client':order.client,
                        'adresse':order.adresse,
                        'fiscal_position': order.fiscal_position.id,
                        'agence_id': order.agence_id.id,
                        })
        else:
            res.update({'client':order.client,
                        'adresse':order.adresse,
                        'fiscal_position': order.fiscal_position.id,
                        'agence_id': order.agence_id.id,
                        })
        return res


    def _prepare_procurement_group(self, cr, uid, order, context=None):
        res = super(sale_order,self)._prepare_procurement_group(cr, uid, order, context=context)
        if order.affaire:
            res.update({'affaire':order.affaire.id, 
                        'client': order.client,
                        'fiscal_position': order.fiscal_position.id,
                        'agence_id': order.agence_id.id,
                        })
        else:
            res.update({'client':order.client,
                        'adresse':order.adresse,
                        'fiscal_position': order.fiscal_position.id,
                        'agence_id': order.agence_id.id,
                        })
        return res
        
    
class account_invoice(osv.osv):
    _inherit="account.invoice"
    
    
    
    def _get_discount(self, cr, uid, ids, odometer_id, arg, context):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr,uid,ids,context=context):
            
            res[record.id] = sum([x.discount * x.price_unit * quantity for x in record.invoice_line])
        return res

        
    _columns = {
        'affaire' : fields.many2one('sale.affaire','Affaire', ondelete="restrict"),
        'client' : fields.char('Nom Client'),
        'adresse' : fields.text('Adresse client'),
        'voucher_ids': fields.one2many('account.voucher','invoice_id','Réglements'),
       # 'amount_discount': fields.function(_get_discount, string="Remise", type='float', store=True),
        
    } 
#    @api.model
#    def _default_journal(self):
#        inv_type = self._context.get('type', 'out_invoice')
#        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
#        company_id = self._context.get('company_id', self.env.user.company_id.id)
#        domain = [
#            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
#            ('company_id', '=', company_id),
#            
#        ]
#        
#        if self._context.get('auth',False) :
#            domain+=[('agence_id','!=',False)]
#        return self.env['account.journal'].search(domain, limit=1)
    
    def search_read(self,cr,uid, domain=None, fields=None, offset=0,limit=None, order=None,context=None):
        
        if 'auth' in context  and context.get('auth',False) and uid != 1:
            if domain:
                company_id = self.pool['res.users'].browse(cr,1, uid).company_id
                domain = domain + ['|',('user_id.company_id','=',company_id.id),('create_uid.company_id','=',company_id.id)]
        
        res = super(account_invoice,self).search_read(cr,uid,domain,fields,offset,limit,order,context)
        return res
    
    def name_get(self, cr, uid, ids, context=None):
        return super(account_invoice,self).name_get( cr, 1, ids, context)

    def _interpolation_dict_context(self, t, context=None):
        if context is None:
            context = {}
        t = Fields.Datetime.from_string(t) or datetime.now()
        sequences = {
            'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
            'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
        }
        return {key: t.strftime(sequence) for key, sequence in sequences.iteritems()}
    
    @api.onchange('internal_number','journal_id')
    def _onchange_int_num(self):
        seq = self.journal_id.sequence_id
        d = self._interpolation_dict_context(self.date_invoice, context=None)
        #d =  self.date_invoice
        prefix = seq._interpolate(seq.prefix, d)
        if self.internal_number:
            if not self.date_invoice and self.internal_number:
                self.internal_number = False
                return {'warning': {'title':u"Date facture erronée",
                                    'message':" Choisir une date avant de saisir le No de facture ! "},}
            
            if self.internal_number.find(prefix)<0:
                self.internal_number = False
                return {'warning': {'title':u"No facture erroné",
                                    'message':" le code doit commencer par (%s) , sinon il faut changer le journal" % prefix},}
            
            try :
                int(self.internal_number.replace(prefix,''))
            except:
                self.internal_number = False
                return {'warning': {'title':u"No facture erroné",
                                    'message':" le code doit commencer par (%s) , sinon il faut changer le journal" % prefix},}
            
            if not self.search([('internal_number','ilike',prefix),('internal_number','>',self.internal_number)]):
                self.internal_number = False
                return {'warning': {'title':u"No facture erroné",
                                    'message':u" Choisissez un numéro déjà existant sinon laissez vide; le système créera le code automatiquement"},}
            
            if  self.search([('internal_number','=',self.internal_number)]):
                self.internal_number = False
                return {'warning': {'title':u"No facture erroné",
                                    'message':u" Numéro déjà attribué, vidé le champs (numéro interne) dans la facture origine que vous voulez remplacer !"},}
                
            if False and self.search([('internal_number','ilike',prefix),'|','&',('internal_number','>',self.internal_number),('date_invoice','<',self.date_invoice),'&',('internal_number','<',self.internal_number),('date_invoice','>',self.date_invoice)]):
                self.internal_number = False
                return {'warning': {'title':u"Date érronée",
                                    'message':u" Choisissez une date dans la série"},}
            
            
    #@api.multi
    def onchange_company_id(self,cr,uid,ids, company_id, part_id, type, invoice_line, currency_id,agence_id = False , context=None):
        res = super(account_invoice,self).onchange_company_id(cr,uid,ids,company_id,part_id,type,invoice_line, currency_id,context=context)
        domain  = 'journal_id' in res['domain'] and res['domain']['journal_id'] or []
        if not context:
            context = {}
        domain += context and context.get("domain",False) and "journal_id" in context.get("domain") and context['domain']['journal_id'] or [] 
        if agence_id:
            domain += ['|',('agence_id','=',agence_id),('agence_id','=',False)]
        values = 'value' in res and res['value'] or {}
        if domain:
            journals = self.pool['account.journal'].search(cr,uid,domain)
            values['journal_id'] = self.pool['account.journal'].browse(cr,uid,journals)[0]
        
        res['value'] = values
            
        
        res['domain'] = {'journal_id': domain}
        
        return res
            
class stock_picking(osv.osv):
    _inherit="stock.picking"
    _columns = {
        #'affaire' : fields.many2one('sale.affaire','Affaire', ondelete="restrict"),
        'fiscal_position' : fields.related('group_id','fiscal_position',relation='account.fiscal.position',type="many2one",string="Fiscal Position"  ),
   
    }  

class account_voucher(osv.osv):
    _inherit="account.voucher"
    _columns = {
        'affaire' : fields.many2one('sale.affaire','Affaire', ondelete="restrict"),
	    'client' : fields.char('Nom Client'),
        'adresse' : fields.text('Adresse Client'),
        'invoice_id': fields.many2one('account.invoice','Facture'),
    } 

class procurement_group(osv.osv):

    _inherit="procurement.group"
    _columns = {
        'affaire' : fields.many2one('sale.affaire','Affaire', ondelete="restrict"),
        'client' : fields.char('Nom Client'),
        'adresse' : fields.text('Adresse Client'),
        'fiscal_position' : fields.many2one('account.fiscal.position',string="Fiscal Position"  ),
    }    

class stock_picking(osv.osv):
    _inherit="stock.picking"
    _columns = {
        'affaire' : fields.related('group_id','affaire', relation='sale.affaire',type='many2one',string='Affaire'),
        'client' :  fields.related('group_id','client',  type='char',string ='Nom Client'),
        'adresse' :  fields.related('group_id','adresse',  type='char',string ='Adresse Client'),


    }      
    

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    def calcul_ttc(self,cr,uid,ids,name,arg,context=None):
        res = {}
        for o in self.browse(cr,uid,ids):
            mtt_ttc = (o.product_uom_qty * o.price_unit ) * (1- o.discount/100) 
            res[o.id] = mtt_ttc
        return res
    
    _columns = {
        'stock_group' : fields.float(u'Dispo. groupe'),
        'stock_depot' : fields.float(u'Dispo. dépôt'),
        'mtt_ttc'     : fields.function(calcul_ttc, string=u'Montant TTC',type="float", store=True),
        'tarif'      : fields.float("Tarif applicable"),
    
    }
    
    
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False,
        lang=False, update_tax=True,
        date_order=False, packaging=False,
        fiscal_position=False, flag=False,
        context=None):
        
        res = super(sale_order_line,self).product_id_change( cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, 
            partner_id,
            lang, update_tax,
            date_order, packaging,
            fiscal_position, flag,
            context)
        
    
        if partner_id:
            client = self.pool['res.partner'].browse(cr,uid,partner_id)
        zone_id = context.get('zone',False)
        if zone_id :
            zone = self.pool['res.partner.zone'].browse(cr,uid,zone_id)
        else:
            zone = client.zone or False
        shipping = context.get('shipping',False) or 'rendu'
        
        part_categ = self.pool['res.partner.category'].browse(cr,uid,context.get('part_categ',[])) or []
        prix = product and self.pool['product.tarif']._get_price(cr ,1, [], product,client=client,zone=zone,shipping=shipping,part_categ=part_categ ) or False
        
        
        if prix:
            res['value']['price_unit'] = prix[1] or False
            res['value']['tarif'] = prix[1] or False
        
        res['value']['product_uos']     = 'product_uom'     in res['value'] and res['value']['product_uom']     or False
        res['value']['product_uos_qty'] = 'product_uom_qty' in res['value'] and res['value']['product_uom_qty'] or 0
        return res

    def create(self,cr,uid,vals,context=None):
        if True or uid in( 1,230):
            order = self.pool['sale.order'].browse(cr,uid,vals['order_id'])
            tax = [x for x in vals['tax_id'] if x[2] != []]
            if tax == [] and 'product_id' in vals:
                company_id = order.company_id
                account_id = self.pool['product.product'].browse(cr,uid,vals['product_id']).categ_id.property_account_income_categ
                if account_id:
                    vals['tax_id'] = [(6,0,[ x.id for x in account_id.tax_ids])] or tax
        
        return super(sale_order_line,self).create(cr,uid,vals,context)
        
class nabi_controle_facture(osv.osv):
    _auto=False
    _name="nabi.controle.facture"
    _columns={
        'id':               fields.integer('ID'),
        'internal_number' : fields.char('Facture'),
        'date_invoice':     fields.date('Date'),
        'seq':              fields.char('Seq'),
        'cnt':              fields.integer('Compteur'),    
        'state' :           fields.char('State'),
        'case':             fields.char('dispo'),    
        'societe':          fields.char('Agence'),
        'err':              fields.char('Erreurs'),
    }
    
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'nabi_controle_facture')
        cr.execute("""
            
            CREATE OR REPLACE VIEW nabi_controle_facture AS (
            
            with a as (
            select  internal_number,
                    date_invoice,
                    substring(internal_number from  '#"F___#"%' for '#') as seq, 
                    substring(replace(internal_number,'bis','') from '%#"0_____#"' for '#')::integer as cnt, 
                    state, res_agence.name as societe
            FROM account_invoice, res_agence
            where account_invoice.agence_id=res_agence.id and account_invoice.type = 'out_invoice'
            order by internal_number,date_invoice
            
            )
            select row_number() OVER () as id, * , case when cnt - lag(cnt) over(partition by seq order by internal_number) != 1 then '[' || lag(cnt) over(partition by seq) ::varchar||'-'||cnt || ']  au  '|| lag(date_invoice) over(partition by seq) when state='cancel' then 'cancel' end , case when lag(date_invoice) over(partition by seq) > date_invoice then 'Erreur date' end as err
            from a
            where a.seq is not null
            )"""
            )
                

class nabi_controle_avoir(osv.osv):
    _auto=False
    _name="nabi.controle.avoir"
    _columns={
        'id':                  fields.integer('ID'),
        'internal_number' :    fields.char('facture'),
        'date_invoice':     fields.date('Date'),
        'seq':  fields.char('seq'),
        'cnt':fields.integer('compteur'),    
        'state' : fields.char('state'),
        'case': fields.char('dispo'),    
        'societe': fields.char('Agence'),
        'err':fields.char('Err'),
    }
    
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'nabi_controle_avoir')
        cr.execute("""
            
            CREATE OR REPLACE VIEW nabi_controle_avoir AS (
            
            with a as (select internal_number,date_invoice,substring(internal_number from  '#"F___#"%' for '#') as seq, substring(internal_number from '%#"0_____#"' for '#')::integer as cnt, state, res_agence.name as societe
           FROM account_invoice, res_agence
           where account_invoice.agence_id=res_agence.id and account_invoice.type = 'out_refund'


                order by internal_number,date_invoice)
                select row_number() OVER () as id, * , case when cnt - lag(cnt) over(partition by seq order by internal_number) != 1 then '[' || lag(cnt) over(partition by seq) ::varchar||'-'||cnt || ']  au  '|| lag(date_invoice) over(partition by seq) when state='cancel' then 'cancel' end , case when lag(date_invoice) over(partition by seq) > date_invoice then 'Erreur date' end as err
                from a
                where a.seq is not null
                )""")
                
    
    

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    def calcul_ttc(self,cr,uid,ids,name,arg,context=None):
        res = {}
        for o in self.browse(cr,uid,ids):
            res[o.id] = {'mtt_ttc':False,
                        'mtt_ht':False,
                        'mtt_remise':False,
                        'mtt_tax': False,
                        'pu_ht': False,
                        }
            mtt_ttc = (o.quantity * o.price_unit ) * (1- o.discount/100) 
            taxes = o.invoice_line_tax_id.compute_all(o.price_unit, o.quantity, product=o.product_id.id, partner=o.invoice_id.partner_id.id)
            
            
            res[o.id]['mtt_ttc'] = mtt_ttc
            
            res[o.id]['mtt_ht'] = taxes['total']
            res[o.id]['mtt_remise'] = taxes['total'] - o.price_subtotal
            res[o.id]['mtt_tax'] = mtt_ttc  - o.price_subtotal
            if o.quantity==0:
                res[o.id]['pu_ht'] =0
            else:
                res[o.id]['pu_ht'] = o.price_subtotal/o.quantity
            
        return res
    
    _columns = {
        'mtt_ttc':      fields.function(calcul_ttc, string=u'Montant TTC',type="float", store=True, multi="cal"),
        'mtt_ht':       fields.function(calcul_ttc,string=u"Montant HT non-remisé",type="float", store=True, multi="cal"),
        'mtt_remise':   fields.function(calcul_ttc,string=u"Montant remise",type="float", store=True, multi="cal"),
        'mtt_tax':      fields.function(calcul_ttc,string=u"Montant tax",type="float", store=True, multi="cal"),
        'pu_ht':      fields.function(calcul_ttc,string=u"Prix Unitaire HT",type="float", store=True, multi="cal"),
    
    }                  
    

            
    
     
    
class account_journal(osv.osv):
    _inherit = "account.journal"
    
    def name_get(self, cr, user, ids, context=None):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}
        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param ids: list of ids for which name should be read
        @param context: context arguments, like lang, time zone
        @return: Returns a list of tupples containing id, name
        """
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        for rs in result:
            if rs.agence_id:
                agence = rs.agence_id
            else:
                agence = rs.company_id.agence_id
            name = "%s (%s)" % (rs.name, agence.name)
            res += [(rs.id, name)]
        return res


class account_move_line(osv.osv):
    _inherit="account.move.line"
    
    def list_partners_to_reconcile(self, cr, uid, context=None, filter_domain=False):
        line_ids = []
        if filter_domain:
            line_ids = self.search(cr, uid, filter_domain, context=context)
        # ligne suivante ajoutée
        ids = [x.partner_id.id for x in self.browse(cr,uid,line_ids,context=context)]
        
#        where_clause = filter_domain and "AND l.id = ANY(%s)" or ""
#        cr.execute(
#             """SELECT partner_id FROM (
#                SELECT l.partner_id, p.last_reconciliation_date, SUM(l.debit) AS debit, SUM(l.credit) AS credit, MAX(l.create_date) AS max_date
#                FROM account_move_line l
#                RIGHT JOIN account_account a ON (a.id = l.account_id)
#                RIGHT JOIN res_partner p ON (l.partner_id = p.id)
#                    WHERE a.reconcile IS TRUE
#                    AND l.reconcile_id IS NULL
#                    AND l.state <> 'draft'
#                    %s
#                    GROUP BY l.partner_id, p.last_reconciliation_date
#                ) AS s
#                WHERE debit > 0 AND credit > 0 AND (last_reconciliation_date IS NULL OR max_date > last_reconciliation_date)
#                ORDER BY last_reconciliation_date"""
#            % where_clause, (line_ids,))
#        ids = [x[0] for x in cr.fetchall()]
        if not ids:
            return []

        # To apply the ir_rules
        partner_obj = self.pool.get('res.partner')
        ids = partner_obj.search(cr, uid, [('id', 'in', ids)], context=context)
        return partner_obj.name_get(cr, uid, ids, context=context)

    
