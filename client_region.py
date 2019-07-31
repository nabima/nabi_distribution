# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp import api, models
from openerp import tools
    
class res_region(osv.osv):
    _name = 'res.region'    
    _columns = {
        'name': fields.char('region'),    
    }

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = { 
        'region': fields.many2one('res.region',u"Region client"),
    }


            
            
