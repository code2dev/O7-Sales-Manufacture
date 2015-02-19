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
        vals["mc_sale_pendientes"] = vals["product_uom_qty"]
        return super(sale_order_line, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        
        if context is not None and context.has_key("sale_id"):
            
            if vals.has_key("order_id"):
                del vals["order_id"]
            
            if type(ids) is list:
                ids = ids[0]
            
            this = self.browse(cr, uid, ids, context=context) 
            total = this["product_uom_qty"]
            pendientes = this["mc_sale_pendientes"]
        
            if vals.has_key("mc_sale_entregados"):
                entregados = vals["mc_sale_entregados"]
                
                if entregados > pendientes:
                    raise osv.except_osv('Error', 'La cantidad a entregar debe ser <= a la cantidad pendiente.')
                else:
                    pendientes = pendientes - entregados
                    vals["mc_sale_pendientes"] = pendientes
                    vals["mc_sale_entregados"] = 0
            
            
            #Verificamos si ya se entregaron todos los productos.
            sale_id = context["sale_id"]   
            sale_obj = self.pool.get("sale.order")
             
            order_line_ids = self.search(cr, uid, [("order_id", "=", sale_id)], context=context)
            
            status_entrega = False
            
            for id_line in order_line_ids:
                line = self.browse(cr, uid, id_line, context=context)
                if line["mc_sale_pendientes"] > 0:
                    status_entrega = True
                    break
            
            if status_entrega:
                sale_obj.write(cr, uid, sale_id, {"entrega_state" : "done"}, context=context)
            else:
                sale_obj.write(cr, uid, sale_id, {"entrega_state" : "parcial"}, context=context)
                          
        return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)        
    
sale_order_line()

class mc_sales_wizard(osv.osv_memory):    

    _name = "mc.sales.wizard"
    
    def action_save_sale_wizard(self, cr, uid, ids, context=None):
        return True
    
    def action_save_sale_wizard_all(self, cr, uid, ids, context=None):
        
        this = self.browse(cr, uid, ids[0], context=context)
        sale_id = this["sale_id"]        
        self.pool.get("sale.order").write(cr, uid, sale_id, {"entrega_state" : "done"}, context=context)        
        return True
    
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