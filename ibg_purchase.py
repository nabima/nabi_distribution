# -*- coding: utf-8 -*-

from openerp.osv import osv,fields
from openerp.tools.translate import _

class purchase_order(osv.osv):
    _inherit="purchase.order"

    def print_bcommande(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'send_rfq')
        return self.pool['report'].get_action(cr, uid, ids, 'purchase.report_purchaseorderlocal', context=context)

    def print_bcommandedcm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'send_rfq')
        return self.pool['report'].get_action(cr, uid, ids, 'purchase.report_purchaseorder_1', context=context)