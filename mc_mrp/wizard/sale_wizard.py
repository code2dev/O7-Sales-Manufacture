from openerp.osv import osv, fields

class sale_order_line(osv.osv):
    
    _inherit = 'sale.order.line'
    
    _columns = {
        "mc_sale_entregados" : fields.float("Entregados", digits=(12,2)),
        "mc_sale_pendientes" : fields.float("Pendientes", digits=(12,2))
    }
    
    _defaults = {  
        'mc_sale_entregados': 0,
        'mc_sale_pendientes': 0,  
    }
    
    def create(self, cr, uid, vals, context=None): 
        return super(self, cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None): 
        return super(self, cr, uid, ids, vals, context=context)
    
sale_order_line()

class mc_sales_wizard(osv.osv_memory):    

    _name = "mc.sales.wizard"
    
    def get_sale_id(self, cr, uid, context=None):
        
        if context and context.has_key("sale_id"):
            return context["sale_id"]
        return False 
    
    def on_change_sale_id(self, cr, uid, ids, sale_id, context=None):
        
        result = {"value" : {}}
        result["value"].update({
            "sale_lines" :  self.pool.get("sale.order.line").search(cr, uid, [("order_id", "=", sale_id)])
        })
        
        return result
        
    _columns = {        
                
        "sale_id" : fields.integer("Id Venta"),
        "sale_lines" : fields.one2many("sale.order.line", "order_id"),        
    }
    
    _defaults = {  
        'sale_id' : get_sale_id,
    }
        
    
mc_sales_wizard()