# -*- coding: utf-8 -*-

from openerp.osv import osv,fields
from bs4 import BeautifulSoup as bs

class ir_ui_view(osv.osv):
    _inherit="ir.ui.view"
    
    
    def pretty_xml(self,cr,uid,ids,context=None):
        context  = context or {}
        
        for o in self.browse(cr,uid,ids):
            
            try:
                x = bs(o.arch,"xml").prettify()
                arch = []
                for xs in x.split("\n"):
                    xss = xs.split('<')
                    xss[0] = ''.join([(xx == ' ' and '\t' or xx) for xx in xss[0]])
                    
                    xss = '<'.join(xss)
                    arch.append(xss)
                o.arch = '\n'.join(arch)
                
            except:
                pass
        return
