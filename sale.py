# -*- coding: utf-8 -*-

from openerp.osv import osv,fields
from openerp.exceptions import  Warning
from openerp.models import NewId
from openerp import tools
from openerp import api, models

class sale_order(osv.osv):
    _inherit= 'sale.order'
    
    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
        return {
            'name': line.name,
            'origin': order.name,
            'date_planned': date_planned,
            'product_id': line.product_id.id,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': line.product_uom_qty,
            'product_uos':  line.product_uom.id,
            'company_id': order.company_id.id,
            'group_id': group_id,
            'invoice_state': (order.order_policy == 'picking') and '2binvoiced' or 'none',
            'sale_line_id': line.id
        }

    @api.onchange('agence_id')
    def onchange_agence_id(self):
        agence_id = self.agence_id.id or self.env.user.agence_id.id
        self.warehouse_id = self.env['stock.warehouse'].search([('agence_id','=',agence_id)])[0]
        self.x_zone = self.partner_id.zone and self.partner_id.zone[0] or   self.company_id.x_zone
        #self.x_zone = self.partner_id.zone and self.partner_id.zone[0] or   self.agence_id.zone_id
        

class sale_order_line(osv.osv):
    _inherit= 'sale.order.line'
    
    def _get_line_qty(self, cr, uid, line, context=None):
        
        return line.product_uom_qty
    
    def _get_line_uom(self, cr, uid, line, context=None):
        
        return line.product_uom.id
    
    

