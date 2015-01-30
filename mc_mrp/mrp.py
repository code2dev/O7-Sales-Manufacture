from openerp.osv import osv, fields

class mrp_bom_types(osv.osv):
    _name = "mrp.bom.types"
    
    _columns = {
        "name" : fields.char("Nombre")
    }
    
mrp_bom_types()

class mrp_bom(osv.osv):
    
    _inherit = "mrp.bom"
    _columns = {
        "tipo_ldm" : fields.many2one("mrp.bom.types", "Tipo de Lista")
    }
    

mrp_bom()


class mc_mrp_product_produce(osv.osv_memory):
    _inherit = "mrp.product.produce"
    
    def do_produce(self, cr, uid, ids, context=None):        
        """ Para calcular el costo total de la fabricacion al terminar el proceso de consumir los materiales
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return: A super function
        """
        mrp_id = context.get('active_id', False)        
        self.pool.get("mrp.production").action_calculate_mrp_price(cr, uid, [mrp_id], context=context)        
        return super(mc_mrp_product_produce, self).do_produce(cr, uid, ids, context=context)    
    
mc_mrp_product_produce()

class mc_mrp_production(osv.osv):
    _inherit = "mrp.production"
    
    def _make_production_consume_line(self, cr, uid, production_line, parent_move_id, source_location_id=False, context=None):
        
        move_id = super(mc_mrp_production, self)._make_production_consume_line(cr, uid, production_line, parent_move_id, source_location_id=False, context=context)        
        mo = self.browse(cr, uid, production_line.production_id.id)
        
        location = None
        values = {}
        
        for line in mo.bom_id.bom_lines:            
            if line.product_id.id == production_line.product_id.id:
                if line.location_id:
                    location = line.location_id.id
                break            
                 
        if location is not None:
            values = {"location_id" : location}
    
        p_qty = production_line.product_qty
        p_cost = production_line.product_id.standard_price
        p_total = p_qty * p_cost
        
        vals = {"product_cost" : p_cost, "product_cost_total" : p_total}        
        vals.update(values)
        
        self.pool.get("stock.move").write(cr, uid, move_id, vals, context=context)        
        return move_id
        
    def action_confirm(self, cr, uid, ids, context=None):
                
        shipment_id = super(mc_mrp_production, self).action_confirm(cr, uid, ids, context=None)        
        self.action_calculate_mrp_price(cr, uid, ids, context=context)        
        return shipment_id
        
    def action_calculate_mrp_price(self, cr, uid, ids, context=None):
        
        mrp_list = self.browse(cr, uid, ids, context)
        result = {}
        
        for produccion in mrp_list:
                        
            result[produccion.id] = {
                'mrp_cost': 0.0,                
            }
            
            mrp_pr_lines = produccion.move_lines
            mrp_pr_lines_consumed = produccion.move_lines2
            
            for move in mrp_pr_lines:
                qty = move.product_qty
                price = move.product_id.standard_price
                total = qty * price
                self.pool.get("stock.move").write(cr, uid, move.id, {"product_cost" : price, "product_cost_total" : total}, context=context)
                result[produccion.id]['mrp_cost'] += total
                 
            for move in mrp_pr_lines_consumed:
                qty = move.product_qty
                price = move.product_id.standard_price
                total = qty * price
                self.pool.get("stock.move").write(cr, uid, move.id, {"product_cost" : price, "product_cost_total" : total}, context=context)
                result[produccion.id]['mrp_cost'] += total
            
            self.write(cr, uid, produccion.id, {"mrp_cost" : result[produccion.id]['mrp_cost']}, context)
            
        return True
    
    _columns = {
        "mrp_cost": fields.float("Costo", digits=(12,2)),
        "product_cost": fields.float("Costo", digits=(12,2)),
    }    

mc_mrp_production()