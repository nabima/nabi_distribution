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

from openerp import tools
import openerp.addons.decimal_precision as dp
from openerp.osv import fields,osv




class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
    
        'regime' : fields.selection(selection=[('a','A'),('b','B')] , string="Regime", default=False)
    }
    
    
    
class nabi_account_invoice_report(osv.osv):
    _name = "nabi.account.invoice.report"
    _description = "Invoices Statistics"
    _auto = False
    _rec_name = 'date'

    def _compute_amounts_in_user_currency(self, cr, uid, ids, field_names, args, context=None):
        """Compute the amounts in the currency of the user
        """
        if context is None:
            context={}
        currency_obj = self.pool.get('res.currency')
        currency_rate_obj = self.pool.get('res.currency.rate')
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        user_currency_id = user.company_id.currency_id.id
        currency_rate_id = currency_rate_obj.search(
            cr, uid, [
                ('rate', '=', 1),
                '|',
                    ('currency_id.company_id', '=', user.company_id.id),
                    ('currency_id.company_id', '=', False)
                ], limit=1, context=context)[0]
        base_currency_id = currency_rate_obj.browse(cr, uid, currency_rate_id, context=context).currency_id.id
        res = {}
        ctx = context.copy()
        for item in self.browse(cr, uid, ids, context=context):
            ctx['date'] = item.date
            price_total = currency_obj.compute(cr, uid, base_currency_id, user_currency_id, item.price_total, context=ctx)
            price_average = currency_obj.compute(cr, uid, base_currency_id, user_currency_id, item.price_average, context=ctx)
            residual = currency_obj.compute(cr, uid, base_currency_id, user_currency_id, item.residual, context=ctx)
            res[item.id] = {
                'user_currency_price_total': price_total,
                'user_currency_price_average': price_average,
                'user_currency_residual': residual,
            }
        return res

    _columns = {
        'date': fields.date('Date', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_qty':fields.float(u'Quantité', readonly=True),
        'uom_name': fields.char('Reference Unit of Measure', size=128, readonly=True),
        'payment_term': fields.many2one('account.payment.term', 'Payment Term', readonly=True),
        'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], readonly=True),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
        'categ_id': fields.many2one('product.category','Category of Product', readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'commercial_partner_id': fields.many2one('res.partner', 'Partner Company', help="Commercial Entity"),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'price_total': fields.float('Total Without Tax', readonly=True),
        'user_currency_price_total': fields.function(_compute_amounts_in_user_currency, string="Total HT", type='float', digits_compute=dp.get_precision('Account'), multi="_compute_amounts"),
        'price_average': fields.float('PU Moyenne', readonly=True, group_operator="avg"),
        'user_currency_price_average': fields.function(_compute_amounts_in_user_currency, string="Average Price", type='float', digits_compute=dp.get_precision('Account'), multi="_compute_amounts"),
        'currency_rate': fields.float('Currency Rate', readonly=True),
        'nbr': fields.integer('NB. Factures', readonly=True),  
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', readonly=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Done'),
            ('cancel','Cancelled')
            ], 'Invoice Status', readonly=True),
        'date_due': fields.date('Due Date', readonly=True),
        'account_id': fields.many2one('account.account', 'Account',readonly=True),
        'account_line_id': fields.many2one('account.account', 'Account Line',readonly=True),
        'partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account',readonly=True),
        'residual': fields.float('Total Residual', readonly=True),
        'user_currency_residual': fields.function(_compute_amounts_in_user_currency, string="Solde", type='float', digits_compute=dp.get_precision('Account'), multi="_compute_amounts"),
        'country_id': fields.many2one('res.country', 'Country of the Partner Company'),
        'agence': fields.many2one('res.agence',string="Agence", readonly=True),
        'regime': fields.char('Regime', readonly=True),
        'categorie_client': fields.many2one('res.partner.category',u'Catégorie Client', readonly=True),
        'ville_client': fields.char('Ville client', readonly=True),
        'price_total_ttc': fields.float('Total TTC', readonly=True),
    }    
    _order = 'date desc'

    _depends = {
        'account.invoice': [
            'account_id', 'amount_total', 'commercial_partner_id', 'company_id',
            'currency_id', 'date_due', 'date_invoice', 'fiscal_position',
            'journal_id', 'partner_bank_id', 'partner_id', 'payment_term',
            'period_id', 'residual', 'state', 'type', 'user_id',
        ],
        'account.invoice.line': [
            'account_id', 'invoice_id', 'price_subtotal', 'product_id',
            'quantity', 'uos_id',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
        'product.uom': ['category_id', 'factor', 'name', 'uom_type'],
        'res.currency.rate': ['currency_id', 'name'],
        'res.partner': ['country_id'],
    }

    

    def init(self, cr):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(cr, 'nabi_account_invoice_report')
        cr.execute("""CREATE or REPLACE VIEW nabi_account_invoice_report as (
 WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                SELECT r.currency_id, r.rate, r.name AS date_start,
                    (SELECT name FROM res_currency_rate r2
                     WHERE r2.name > r.name AND
                           r2.currency_id = r.currency_id
                     ORDER BY r2.name ASC
                     LIMIT 1) AS date_end
                FROM res_currency_rate r
            ),          
        
 sub as (SELECT min(ail.id) AS id,
            ai.date_invoice AS date,
            ail.product_id,
            ai.partner_id,
            ai.payment_term,
            ai.period_id,
            u2.name AS uom_name,
            ai.currency_id,
            ai.journal_id,
            ai.fiscal_position,
            ai.user_id,
            ai.company_id,
            count(ail.*) AS nbr,
            ai.type,
            ai.state,
            pt.categ_id,
            ai.date_due,
            ai.account_id,
            ail.account_id AS account_line_id,
            ai.partner_bank_id,
            sum(
                CASE
                    WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN (- ail.quantity) / u.factor * u2.factor
                    ELSE ail.quantity / u.factor * u2.factor
                END) AS product_qty,
            sum(
                CASE
                    WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN - ail.price_subtotal
                    ELSE ail.price_subtotal
                END) AS price_total,
                CASE
                    WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN sum(- ail.price_subtotal)
                    ELSE sum(ail.price_subtotal)
                END /
                CASE
                    WHEN sum(ail.quantity / u.factor * u2.factor) <> 0::numeric THEN
                    CASE
                        WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN sum((- ail.quantity) / u.factor * u2.factor)
                        ELSE sum(ail.quantity / u.factor * u2.factor)
                    END
                    ELSE 1::numeric
                END AS price_average,
                CASE
                    WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN - ai.residual
                    ELSE ai.residual
                END / (( SELECT count(*) AS count
                   FROM account_invoice_line l
                  WHERE l.invoice_id = ai.id))::numeric * count(*)::numeric AS residual,
            ai.commercial_partner_id,
            partner.country_id,
            ai.section_id,
        aj.regime,
        prel.category_id as categorie,
        pag.agence_id as agence,
        partner.city,
        ai.amount_total
           FROM account_invoice_line ail
             JOIN account_invoice ai ON ai.id = ail.invoice_id
             JOIN res_partner partner ON ai.commercial_partner_id = partner.id
             LEFT JOIN product_product pr ON pr.id = ail.product_id
             LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
             LEFT JOIN product_uom u ON u.id = ail.uos_id
             LEFT JOIN product_uom u2 ON u2.id = pt.uom_id
        JOIN account_journal aj ON aj.id = ai.journal_id
        left join res_partner_res_partner_category_rel prel on prel.partner_id = partner.id 
        left join res_partner_agence_rel pag on pag.partner_id = partner.id
          GROUP BY ail.product_id, ai.date_invoice, ai.id, ai.partner_id, ai.payment_term, ai.period_id, u2.name, u2.id, ai.currency_id, ai.journal_id, ai.fiscal_position, ai.user_id, ai.company_id, ai.type, ai.state, pt.categ_id, ai.date_due, ai.account_id, ail.account_id, ai.partner_bank_id, ai.residual, ai.amount_total, ai.commercial_partner_id, partner.country_id, ai.section_id,prel.category_id ,partner.city,
            ai.amount_total,pag.agence_id
,aj.regime
            )

SELECT sub.id,
    sub.date,
    sub.product_id,
    sub.partner_id,
    sub.country_id,
    sub.payment_term,
    sub.period_id,
    sub.uom_name,
    sub.currency_id,
    sub.journal_id,
    sub.fiscal_position,
    sub.user_id,
    sub.company_id,
    sub.nbr,
    sub.type,
    sub.state,
    sub.categ_id,
    sub.date_due,
    sub.account_id,
    sub.account_line_id,
    sub.partner_bank_id,
    sub.product_qty,
    sub.price_total / cr.rate AS price_total,
    sub.price_average / cr.rate AS price_average,
    cr.rate AS currency_rate,
    sub.residual / cr.rate AS residual,
    sub.commercial_partner_id,
    sub.section_id,
    sub.regime,   
    sub.categorie as categorie_client,
    sub.agence,
    sub.city as ville_client,
    sub.amount_total as price_total_ttc
   FROM  sub
     JOIN currency_rate cr ON cr.currency_id = sub.currency_id AND cr.date_start <= COALESCE(sub.date::timestamp with time zone, now()) AND (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date::timestamp with time zone, now()))


            
            )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

