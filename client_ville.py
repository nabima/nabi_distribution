# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp import api, models
from openerp import tools
    
class res_ville(osv.osv):
    _name = 'res.ville'    
    _columns = {
        'name': fields.char('ville'),    
    }

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = { 
        'ville': fields.many2one('res.ville',u"Ville client"),
    }


            
            
