from openerp.osv import osv, fields

class mc_stock_move(osv.osv):
    
    _inherit = 'stock.move'
    
    _columns = {
        "product_cost" : fields.float("Costo", digits=(12,2)),
        "product_cost_total" : fields.float("Total", digits=(12,2))
    }
    
    
mc_stock_move()

class stock_move_consume(osv.osv_memory):

    _inherit = "stock.move.consume"
    
    def do_move_consume(self, cr, uid, ids, context=None):
        
        res = super(stock_move_consume, self).do_move_consume(cr, uid, ids, context=context)
        
        if context is not None and context.has_key("mo"):
            
            mo = self.pool.get("mrp.production")
            stock_move = self.pool.get("stock.move")
            stock_move_id = stock_move.browse(cr, uid, ids[0], context=context) 
            mo_id = mo.search(cr, uid, [("name", "=", context["mo"])], context=context)[0]
            
            producto = stock_move_id.product_id.name
            qty = stock_move_id.product_qty  
            uom = stock_move_id.product_uom
            
            usr_obj = self.pool.get("res.users")
            usr = usr_obj.browse(cr, 1, uid, context=context)
            partner_id = usr.partner_id.id
            
            msg_obj = self.pool.get("mail.message")
            
            data = {
                "attachment_ids" : [],
                "author_id" : partner_id,
                "body" : "<p>Entregado(s) " + str(qty) + " " + uom.name + "(s) de " + producto + "</p>",
                "model" : "mrp.production",
                "parent_id" : msg_obj.search(cr, uid, [("res_id", "=", mo_id), ("parent_id", "=", False)], context=context)[0],
                "partner_ids" : [],
                "res_id" : mo_id,
                "subject" : False,
                "subtype_id" : 1,
                "type" : "comment"
            }
        
            msg_id = msg_obj.create(cr, uid, data, context=context)
        
        return res 

stock_move_consume()

class mc_stock_location(osv.osv):
    
    _inherit = 'stock.location'
    
    _columns = {
        "ubicacion_prestamo" : fields.boolean("Prestamos")        
    }
    
    
mc_stock_location()