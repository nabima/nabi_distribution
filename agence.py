# -*- coding: utf-8 -*-

from openerp.osv import osv,fields
from openerp import tools



class product_pricelist(osv.osv):
    _inherit='product.pricelist'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_followup_followup(osv.osv):
    _inherit='account_followup.followup'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class ir_default(osv.osv):
    _inherit='ir.default'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_voucher(osv.osv):
    _inherit='account.voucher'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_voucher_line(osv.osv):
    _inherit='account.voucher.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_followup_stat_by_partner(osv.osv):
    _inherit='account_followup.stat.by.partner'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_followup_stat_by_partner')
        # Here we don't have other choice but to create a virtual ID based on the concatenation
        # of the partner_id and the company_id, because if a partner is shared between 2 companies,
        # we want to see 2 lines for him in this table. It means that both company should be able
        # to send him follow-ups separately . An assumption that the number of companies will not
        # reach 10 000 records is made, what should be enough for a time.
        cr.execute("""
            create view account_followup_stat_by_partner as (
                SELECT
                    l.partner_id * 10000::bigint + l.company_id as id,
                    l.partner_id AS partner_id,
                    min(l.date) AS date_move,
                    max(l.date) AS date_move_last,
                    max(l.followup_date) AS date_followup,
                    max(l.followup_line_id) AS max_followup_id,
                    sum(l.debit - l.credit) AS balance,
                    l.company_id as company_id,
                    l.agence_id
                FROM
                    account_move_line l
                    LEFT JOIN account_account a ON (l.account_id = a.id)
                WHERE
                    a.active AND
                    a.type = 'receivable' AND
                    l.reconcile_id is NULL AND
                    l.partner_id IS NOT NULL
                    GROUP BY
                    l.partner_id, l.company_id, l.agence_id
            )""")


class multi_company_default(osv.osv):
    _inherit='multi_company.default'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_warehouse(osv.osv):
    _inherit='stock.warehouse'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class res_company(osv.osv):
    _inherit='res.company'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class ir_attachment(osv.osv):
    _inherit='ir.attachment'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class ir_property(osv.osv):
    _inherit='ir.property'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class res_users(osv.osv):
    _inherit='res.users'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_followup_print(osv.osv):
    _inherit='account_followup.print'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_followup_stat(osv.osv):
    _inherit='account_followup.stat'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_followup_stat')
        cr.execute("""
            create or replace view account_followup_stat as (
                SELECT
                    l.id as id,
                    l.partner_id AS partner_id,
                    min(l.date) AS date_move,
                    max(l.date) AS date_move_last,
                    max(l.followup_date) AS date_followup,
                    max(l.followup_line_id) AS followup_id,
                    sum(l.debit) AS debit,
                    sum(l.credit) AS credit,
                    sum(l.debit - l.credit) AS balance,
                    l.company_id AS company_id,
                    l.agence_id,
                    l.blocked as blocked,
                    l.period_id AS period_id
                FROM
                    account_move_line l
                    LEFT JOIN account_account a ON (l.account_id = a.id)
                WHERE
                    a.active AND
                    a.type = 'receivable' AND
                    l.reconcile_id is NULL AND
                    l.partner_id IS NOT NULL
                GROUP BY
                    l.id, l.partner_id, l.company_id, l.agence_id, l.blocked, l.period_id
            )""")

class res_partner(osv.osv):
    _inherit='res.partner'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class document_directory(osv.osv):
    _inherit='document.directory'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class resource_calendar(osv.osv):
    _inherit='resource.calendar'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_bank_statement(osv.osv):
    _inherit='account.bank.statement'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class resource_resource(osv.osv):
    _inherit='resource.resource'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_price_history(osv.osv):
    _inherit='product.price.history'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_template(osv.osv):
    _inherit='product.template'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_bank_statement_line(osv.osv):
    _inherit='account.bank.statement.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class res_currency(osv.osv):
    _inherit='res.currency'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_pricelist_version(osv.osv):
    _inherit='product.pricelist.version'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_inventory_line(osv.osv):
    _inherit='stock.inventory.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_account(osv.osv):
    _inherit='account.account'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_quant_package(osv.osv):
    _inherit='stock.quant.package'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_warehouse_orderpoint(osv.osv):
    _inherit='stock.warehouse.orderpoint'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_fiscalyear(osv.osv):
    _inherit='account.fiscalyear'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class purchase_report(osv.osv):
    _inherit='purchase.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'purchase_report')
        cr.execute("""
            create or replace view purchase_report as (
                WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                    SELECT r.currency_id, r.rate, r.name AS date_start,
                        (SELECT name FROM res_currency_rate r2
                        WHERE r2.name > r.name AND
                            r2.currency_id = r.currency_id
                         ORDER BY r2.name ASC
                         LIMIT 1) AS date_end
                    FROM res_currency_rate r
                )
                select
                    min(l.id) as id,
                    s.date_order as date,
                    l.state,
                    s.date_approve,
                    s.minimum_planned_date as expected_date,
                    s.dest_address_id,
                    s.pricelist_id,
                    s.validator,
                    spt.warehouse_id as picking_type_id,
                    s.partner_id as partner_id,
                    s.create_uid as user_id,
                    s.company_id as company_id,
                    s.agence_id,
                    l.product_id,
                    t.categ_id as category_id,
                    t.uom_id as product_uom,
                    s.location_id as location_id,
                    sum(l.product_qty/u.factor*u2.factor) as quantity,
                    extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr,
                    sum(l.price_unit/cr.rate*l.product_qty)::decimal(16,2) as price_total,
                    avg(100.0 * (l.price_unit/cr.rate*l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,
                    sum(ip.value_float*l.product_qty/u.factor*u2.factor)::decimal(16,2) as price_standard,
                    (sum(l.product_qty*l.price_unit/cr.rate)/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average
                from purchase_order_line l
                    join purchase_order s on (l.order_id=s.id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                            LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.template,',t.id) AND ip.company_id=s.company_id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join stock_picking_type spt on (spt.id=s.picking_type_id)
                    join currency_rate cr on (cr.currency_id = s.currency_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
                group by
                    s.company_id,
                    s.agence_id,
                    s.create_uid,
                    s.partner_id,
                    u.factor,
                    s.location_id,
                    l.price_unit,
                    s.date_approve,
                    l.date_planned,
                    l.product_uom,
                    s.minimum_planned_date,
                    s.pricelist_id,
                    s.validator,
                    s.dest_address_id,
                    l.product_id,
                    t.categ_id,
                    s.date_order,
                    l.state,
                    spt.warehouse_id,
                    u.uom_type,
                    u.category_id,
                    t.uom_id,
                    u.id,
                    u2.factor
            )
        """)
class procurement_rule(osv.osv):
    _inherit='procurement.rule'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class procurement_order(osv.osv):
    _inherit='procurement.order'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    
class procurement_group(osv.osv):

    _inherit="procurement.group"
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    
class account_period(osv.osv):
    _inherit='account.period'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_tax_code(osv.osv):
    _inherit='account.tax.code'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_fiscal_position(osv.osv):
    _inherit='account.fiscal.position'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_tax(osv.osv):
    _inherit='account.tax'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_journal(osv.osv):
    _inherit='account.journal'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_journal_period(osv.osv):
    _inherit='account.journal.period'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_move(osv.osv):
    _inherit='account.move'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_model(osv.osv):
    _inherit='account.model'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_installer(osv.osv):
    _inherit='account.installer'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class res_partner_bank(osv.osv):
    _inherit='res.partner.bank'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_analytic_line(osv.osv):
    _inherit='account.analytic.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_common_partner_report(osv.osv):
    _inherit='account.common.partner.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_common_journal_report(osv.osv):
    _inherit='account.common.journal.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_common_account_report(osv.osv):
    _inherit='account.common.account.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_partner_balance(osv.osv):
    _inherit='account.partner.balance'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_print_journal(osv.osv):
    _inherit='account.print.journal'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_central_journal(osv.osv):
    _inherit='account.central.journal'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_balance_report(osv.osv):
    _inherit='account.balance.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_treasury_report(osv.osv):
    _inherit='account.treasury.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_treasury_report')
        cr.execute("""
            create or replace view account_treasury_report as (
            select
                p.id as id,
                p.fiscalyear_id as fiscalyear_id,
                p.id as period_id,
                sum(l.debit) as debit,
                sum(l.credit) as credit,
                sum(l.debit-l.credit) as balance,
                p.date_start as date,
                am.company_id as company_id,
                am.agence_id
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_period p on (am.period_id=p.id)
            where l.state != 'draft'
              and a.type = 'liquidity'
            group by p.id, p.fiscalyear_id, p.date_start, am.company_id,am.agence_id
            )
        """)

    
    

class analytic_entries_report(osv.osv):
    _inherit='analytic.entries.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'analytic_entries_report')
        cr.execute("""
            create or replace view analytic_entries_report as (
                 select
                     min(a.id) as id,
                     count(distinct a.id) as nbr,
                     a.date as date,
                     a.user_id as user_id,
                     a.name as name,
                     analytic.partner_id as partner_id,
                     a.company_id as company_id,
                     a.agence_id,
                     a.currency_id as currency_id,
                     a.account_id as account_id,
                     a.general_account_id as general_account_id,
                     a.journal_id as journal_id,
                     a.move_id as move_id,
                     a.product_id as product_id,
                     a.product_uom_id as product_uom_id,
                     sum(a.amount) as amount,
                     sum(a.unit_amount) as unit_amount
                 from
                     account_analytic_line a, account_analytic_account analytic
                 where analytic.id = a.account_id
                 group by
                     a.date, a.user_id,a.name,analytic.partner_id,a.company_id, a.agence_id, a.currency_id,
                     a.account_id,a.general_account_id,a.journal_id,
                     a.move_id,a.product_id,a.product_uom_id
            )
        """)

class ir_sequence(osv.osv):
    _inherit='ir.sequence'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_analytic_account(osv.osv):
    _inherit='account.analytic.account'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class wizard_multi_charts_accounts(osv.osv):
    _inherit='wizard.multi.charts.accounts'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_invoice(osv.osv):
    _inherit='account.invoice'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_analytic_journal(osv.osv):
    _inherit='account.analytic.journal'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class sale_receipt_report(osv.osv):
    _inherit='sale.receipt.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_receipt_report')
        cr.execute("""
            create or replace view sale_receipt_report as (
                select min(avl.id) as id,
                    av.date as date,
                    av.partner_id as partner_id,
                    aj.currency as currency_id,
                    av.journal_id as journal_id,
                    rp.user_id as user_id,
                    av.company_id as company_id,
                    av.agence_id,
                    count(avl.*) as nbr,
                    av.type as type,
                    av.state,
                    av.pay_now,
                    av.date_due as date_due,
                    av.account_id as account_id,
                    sum(av.amount-av.tax_amount)/(select count(l.id) from account_voucher_line as l
                            left join account_voucher as a ON (a.id=l.voucher_id)
                            where a.id=av.id) as price_total,
                    sum(av.amount)/(select count(l.id) from account_voucher_line as l
                            left join account_voucher as a ON (a.id=l.voucher_id)
                            where a.id=av.id) as price_total_tax,
                    sum((select extract(epoch from avg(date_trunc('day',aml.date_created)-date_trunc('day',l.create_date)))/(24*60*60)::decimal(16,2)
                        from account_move_line as aml
                        left join account_voucher as a ON (a.move_id=aml.move_id)
                        left join account_voucher_line as l ON (a.id=l.voucher_id)
                        where a.id=av.id)) as delay_to_pay,
                    sum((select extract(epoch from avg(date_trunc('day',a.date_due)-date_trunc('day',a.date)))/(24*60*60)::decimal(16,2)
                        from account_move_line as aml
                        left join account_voucher as a ON (a.move_id=aml.move_id)
                        left join account_voucher_line as l ON (a.id=l.voucher_id)
                        where a.id=av.id)) as due_delay
                from account_voucher_line as avl
                left join account_voucher as av on (av.id=avl.voucher_id)
                left join res_partner as rp ON (rp.id=av.partner_id)
                left join account_journal as aj ON (aj.id=av.journal_id)
                where av.type='sale' and aj.type in ('sale','sale_refund')
                group by
                    av.date,
                    av.id,
                    av.partner_id,
                    aj.currency,
                    av.journal_id,
                    rp.user_id,
                    av.company_id,
                    av.agence_id,
                    av.type,
                    av.state,
                    av.date_due,
                    av.account_id,
                    av.tax_amount,
                    av.amount,
                    av.tax_amount,
                    av.pay_now
            )
        """)

class account_config_settings(osv.osv):
    _inherit='account.config.settings'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_invoice_tax(osv.osv):
    _inherit='account.invoice.tax'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_inventory(osv.osv):
    _inherit='stock.inventory'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_location(osv.osv):
    _inherit='stock.location'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_quant(osv.osv):
    _inherit='stock.quant'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_move(osv.osv):
    _inherit='stock.move'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_location_path(osv.osv):
    _inherit='stock.location.path'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_picking(osv.osv):
    _inherit='stock.picking'
    _columns={
        'agence_id':fields.many2one('res.agence',u'Agence'),
        }
    
    def create(self,cr,uid,vals,context=None):
        agence_id = []
        if 'agence_id' not in vals:
            group_id = 'group_id' in vals and vals['group_id'] and  self.pool['procurement.group'].browse(cr,uid,vals['group_id']) or []
            if group_id :
                agence_id = group_id.agence_id
                
            if not agence_id:
                agence_id = self.pool['res.users'].browse(cr,uid,uid).agence_id
            
            if agence_id:
                vals['agence_id'] = agence_id.id
                
            
            
        
        return super(stock_picking,self).create(cr,uid,vals, context=context)

class account_common_report(osv.osv):
    _inherit='account.common.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_history(osv.osv):
    _inherit='stock.history'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_config_settings(osv.osv):
    _inherit='stock.config.settings'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class payment_acquirer(osv.osv):
    _inherit='payment.acquirer'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_invoice_report(osv.osv):
    _inherit='account.invoice.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class sale_report(osv.osv):
    _inherit='sale.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class sale_order(osv.osv):
    _inherit='sale.order'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    
    def _get_default_agence(self, cr, uid, context=None):
        agence_id = self.pool.get('res.users').browse(cr,uid,uid).agence_id
        if not agence_id:
            raise osv.except_osv(u'Error!', u'There is no default agence for the current user!')
        return agence_id
        
    _defaults = {
        'agence_id' : _get_default_agence,
    }

class sale_order_line(osv.osv):
    _inherit='sale.order.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_location_route(osv.osv):
    _inherit='stock.location.route'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_aged_trial_balance(osv.osv):
    _inherit='account.aged.trial.balance'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_partner_ledger(osv.osv):
    _inherit='account.partner.ledger'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_move_line(osv.osv):
    _inherit='account.move.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_vat_declaration(osv.osv):
    _inherit='account.vat.declaration'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class accounting_report(osv.osv):
    _inherit='accounting.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_general_journal(osv.osv):
    _inherit='account.general.journal'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_report_general_ledger(osv.osv):
    _inherit='account.report.general.ledger'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_entries_report(osv.osv):
    _inherit='account.entries.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_pricelist_item(osv.osv):
    _inherit='product.pricelist.item'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class project_task_work(osv.osv):
    _inherit='project.task.work'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class purchase_order(osv.osv):
    _inherit='purchase.order'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class purchase_order_line(osv.osv):
    _inherit='purchase.order.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class report_project_task_user(osv.osv):
    _inherit='report.project.task.user'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'report_project_task_user')
        cr.execute("""
            CREATE view report_project_task_user as
              SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.date_start as date_start,
                    t.date_end as date_end,
                    t.date_last_stage_update as date_last_stage_update,
                    t.date_deadline as date_deadline,
                    abs((extract('epoch' from (t.write_date-t.date_start)))/(3600*24))  as no_of_days,
                    t.user_id,
                    t.reviewer_id,
                    progress as progress,
                    t.project_id,
                    t.effective_hours as hours_effective,
                    t.priority,
                    t.name as name,
                    t.company_id,
                    t.agence_id,
                    t.partner_id,
                    t.stage_id as stage_id,
                    t.kanban_state as state,
                    remaining_hours as remaining_hours,
                    total_hours as total_hours,
                    t.delay_hours as hours_delay,
                    planned_hours as hours_planned,
                    (extract('epoch' from (t.write_date-t.create_date)))/(3600*24)  as closing_days,
                    (extract('epoch' from (t.date_start-t.create_date)))/(3600*24)  as opening_days,
                    (extract('epoch' from (t.date_deadline-(now() at time zone 'UTC'))))/(3600*24)  as delay_endings_days
              FROM project_task t
                WHERE t.active = 'true'
                GROUP BY
                    t.id,
                    remaining_hours,
                    t.effective_hours,
                    progress,
                    total_hours,
                    planned_hours,
                    hours_delay,
                    create_date,
                    write_date,
                    date_start,
                    date_end,
                    date_deadline,
                    date_last_stage_update,
                    t.user_id,
                    t.reviewer_id,
                    t.project_id,
                    t.priority,
                    name,
                    t.company_id,
                    t.agence_id,
                    t.partner_id,
                    stage_id
        """)

class project_task(osv.osv):
    _inherit='project.task'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class project_project(osv.osv):
    _inherit='project.project'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class stock_reservation(osv.osv):
    _inherit='stock.reservation'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_supplierinfo(osv.osv):
    _inherit='product.supplierinfo'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

#class x_gestion_inventaire(osv.osv):
#    _inherit='x_gestion_inventaire'
#    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}



class inventaire(osv.osv):
    _inherit='inventaire'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_template_tarif_achat(osv.osv):
    _inherit='product.template.tarif.achat'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_template_stock(osv.osv):
    _inherit='product.template.stock'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_template_approvisionner_line(osv.osv):
    _inherit='product.template.approvisionner.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class ir_values(osv.osv):
    _inherit='ir.values'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_template_stock_company(osv.osv):
    _inherit='product.template.stock.company'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class sale_stats_month(osv.osv):
    _inherit='sale.stats.month'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class nabi_account_invoice_report(osv.osv):
    _inherit='nabi.account.invoice.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

#class x_marge_famille(osv.osv):
#    _inherit='x_marge_famille'
#    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class resource_calendar_leaves(osv.osv):
    _inherit='resource.calendar.leaves'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_job(osv.osv):
    _inherit='hr.job'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_department(osv.osv):
    _inherit='hr.department'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_contribution_register(osv.osv):
    _inherit='hr.contribution.register'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_salary_rule_category(osv.osv):
    _inherit='hr.salary.rule.category'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_payroll_structure(osv.osv):
    _inherit='hr.payroll.structure'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_payslip(osv.osv):
    _inherit='hr.payslip'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_salary_rule(osv.osv):
    _inherit='hr.salary.rule'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_payslip_line(osv.osv):
    _inherit='hr.payslip.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_expense_expense(osv.osv):
    _inherit='hr.expense.expense'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_expense_report(osv.osv):
    _inherit='hr.expense.report'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_expense_report')
        cr.execute("""
            create or replace view hr_expense_report as (
                 WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                    SELECT r.currency_id, r.rate, r.name AS date_start,
                        (SELECT name FROM res_currency_rate r2
                        WHERE r2.name > r.name AND
                            r2.currency_id = r.currency_id
                         ORDER BY r2.name ASC
                         LIMIT 1) AS date_end
                    FROM res_currency_rate r
                 )
                 select
                     min(l.id) as id,
                     s.date as date,
                     s.create_date as create_date,
                     s.employee_id,
                     s.journal_id,
                     s.currency_id,
                     s.date_confirm as date_confirm,
                     s.date_valid as date_valid,
                     s.user_valid as user_id,
                     s.department_id,
                     avg(extract('epoch' from age(s.date_valid,s.date)))/(3600*24) as  delay_valid,
                     avg(extract('epoch' from age(s.date_valid,s.date_confirm)))/(3600*24) as  delay_confirm,
                     l.product_id as product_id,
                     l.analytic_account as analytic_account,
                     sum(l.unit_quantity * u.factor) as product_qty,
                     s.company_id as company_id,
                     s.agence_id,
                     sum(l.unit_amount/cr.rate*l.unit_quantity)::decimal(16,2) as price_total,
                     (sum(l.unit_quantity*l.unit_amount/cr.rate)/sum(case when l.unit_quantity=0 or u.factor=0 then 1 else l.unit_quantity * u.factor end))::decimal(16,2) as price_average,
                     count(*) as nbr,
                     (select unit_quantity from hr_expense_line where id=l.id and product_id is not null) as no_of_products,
                     (select analytic_account from hr_expense_line where id=l.id and analytic_account is not null) as no_of_account,
                     s.state
                 from hr_expense_line l
                 left join hr_expense_expense s on (s.id=l.expense_id)
                 left join product_uom u on (u.id=l.uom_id)
                 left join currency_rate cr on (cr.currency_id = s.currency_id and
                        cr.date_start <= coalesce(s.date_confirm, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_confirm, now())))
                 group by
                     s.date,
                     s.create_date,
                     s.date_confirm,
                     s.date_valid,
                     l.product_id,
                     l.analytic_account,
                     s.currency_id,
                     s.user_valid,
                     s.department_id,
                     l.uom_id,
                     l.id,
                     s.state,
                     s.journal_id,
                     s.company_id,
                     s.agence_id,
                     s.employee_id
            )
        """)

#class x_marge_detail(osv.osv):
#    _inherit='x_marge_detail'
#    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class fleet_vehicle(osv.osv):
    _inherit='fleet.vehicle'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class account_invoice_line(osv.osv):
    _inherit='account.invoice.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_product(osv.osv):
    _inherit='product.product'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_remise_line(osv.osv):
    _inherit='product.remise.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class product_frais_line(osv.osv):
    _inherit='product.frais.line'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

class hr_employee(osv.osv):
    _inherit='hr.employee'
    _columns={'agence_id':fields.many2one('res.agence',u'Agence'),}

