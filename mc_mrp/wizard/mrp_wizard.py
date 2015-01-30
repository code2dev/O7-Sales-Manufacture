from openerp.osv import osv, fields

class mc_mrp_bom(osv.osv):
    
    _inherit = 'mrp.bom'
    
    _columns = {
        "venta_wzrd" : fields.integer("Venta"),
        'location_id': fields.many2one('stock.location', 'Ubicacion', select=True),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
       
        if context  and context.has_key("active_model") :   
            if context["active_model"] == "sale.order" and vals.has_key("bom_id"):    
                del vals["bom_id"]          
        
        if vals:
            res = super(mc_mrp_bom, self).write(cr, uid, ids, vals, context=context)
        
        return True
    
    def create(self, cr, uid, values, context=None):
                
        mo_id = None
        
        if context is not None and context.has_key("active_model") :
            if context["active_model"] == "sale.order":
                if values.has_key("bom_id"):
                    mo_id  = values["bom_id"] 
                
                values["bom_id"] = False
                
                product = self.pool.get("product.product").browse(cr, uid, values["product_id"], context=context)
                
                if not values.has_key("product_uom"):
                    uom_id = product.product_tmpl_id.uom_id.id
                    values["product_uom"] = uom_id
                
                if not values.has_key("name"):
                    values["name"] = product.name 
                
        res = super(mc_mrp_bom, self).create(cr, uid, values, context=context)
        
        if mo_id:
            self.write(cr, uid, res, {"venta_wzrd" : mo_id}, context)
        
        return res
    
mc_mrp_bom()

class mc_mrp_material_wizard(osv.osv_memory):    

    _name = "mrp.add.material.wizard"
    
    def notZero(self, cr, uid, ids,context=None): 
        
        this = self.browse(cr, uid, ids, context=context)[0]
        
        if this.product_qty <= 0:
            return False
        
        return True
    
    _constraints = [(notZero, 'Error: La cantidad minima debe ser 1', ['product_qty']), ] 
    
    def action_add_material(self, cr, uid, ids, context=None):        
        
        move_obj = self.pool.get('stock.move')
        ship_obj =  self.pool.get('stock.picking')
        mrp_obj = self.pool.get('mrp.production')
        prod_line_obj = self.pool.get('mrp.production.product.line')
        this = self.browse(cr, uid, ids, context=context)[0]
        product = this.product_id
        
        line = {
                "name" : product.name,
                "product_id" : product.id,
                "product_qty" : this.product_qty,
                "product_uom" : product.product_tmpl_id.uom_id.id,
                "product_uos_qty" : False,
                "product_uos" : False,
                "production_id" : context["mo"],                 
        }
        
        prod_line_id = prod_line_obj.create(cr, uid, line)   
        prod_line = prod_line_obj.browse(cr, uid, prod_line_id, context=context)
        
        move_id = move_obj.search(cr, uid, [("production_id", "=", context["mo"])], context=context)[0]
        move = move_obj.browse(cr, uid, move_id, context=context)        
        shipment_id = ship_obj.search(cr, uid, [("origin", "like", move.name)], context=context)[0]
                
        consume_move_id = mrp_obj._make_production_consume_line(cr, uid, prod_line, move_id, source_location_id=this.location_id.id, context=context)
        move_obj.write(cr, uid, consume_move_id, {"product_cost" : product.standard_price}, context=context)
        
        if shipment_id:
            shipment_move_id = mrp_obj._make_production_internal_shipment_line(cr, uid, prod_line, shipment_id, consume_move_id, destination_location_id=this.location_id.id, context=context)
            mrp_obj._make_production_line_procurement(cr, uid, prod_line, shipment_move_id, context=context)
        
        mrp_obj.action_calculate_mrp_price(cr, uid, [context["mo"]], context=context)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    def product_id_change(self, cr, uid, ids, product_id, context=None):        
        
        result = {}        
        product = self.pool.get("product.product").browse(cr, uid, product_id, context=context)
        result["value"] = {            
            "product_qty" : 1.0,
            "product_uom" : product.product_tmpl_id.uom_id.id,
            "location_id" : False
        }      
            
        return result
    
    _columns = {            
            "product_id" :  fields.many2one("product.product", "Material", required=True),
            "product_qty": fields.float('Cantidad', required=True),
            "product_uom": fields.many2one('product.uom', 'Unidad de Medida', readonly=True),
            "location_id" :  fields.many2one("stock.location", "Ubicacion", required=True),
    }

mc_mrp_material_wizard()

class mc_mrp_wizard(osv.osv_memory):    

    _name = "mrp.production.wizard"
    
    def product_id_change(self, cr, uid, ids, productos_line, context=None):
        
        mrp_obj = self.pool.get("mrp.production")
        sale_line = self.pool.get("sale.order.line")
        result = {}
        
        if productos_line:
            res = sale_line.read(cr, uid, productos_line, ["product_id", "product_uom_qty", "product_uom", "name"])        
            result = mrp_obj.product_id_change(cr, uid, ids, res["product_id"][0], context=context)
        
            result["value"].update({
                "product_qty" : res["product_uom_qty"],
                "product_id" : res["product_id"][0],
                "desc" : res["name"]
            })
            
        else:
            result["value"] = {                
                "product_id" : False,
                "product_qty" : 0,
                "product_uom" : False,
                "bom_id" : False,
                "desc" : ""
            }
        
            
        return result        

    
    def bom_id_change(self, cr, uid, ids, bom_id, context=None):
        
        mrp_obj = self.pool.get("mrp.production")
        bom_obj = self.pool.get("mrp.bom")
        
        result = mrp_obj.bom_id_change(cr, uid, ids, bom_id, context=context)
        if bom_id:
            bom_ids = bom_obj.search(cr, uid, [("bom_id", "=", bom_id)])
        else:
            bom_ids = False
              
        result["value"].update({
            "bom_lines" :  bom_ids
        })
        return result
    
    def get_lineas(self, cr, uid, context=None):
        
        lineas =[]
        
        if context is not None and context.has_key("sale_id"):
            
            sale_line_obj = self.pool.get("sale.order.line")
            lineas = sale_line_obj.search(cr, uid, [("order_id", "=", context["sale_id"])])
                           
        return lineas  
    
    def get_productos(self, cr, uid, context=None):       
        
        line_obj = self.pool.get("sale.order.line")        
        line_ids = self.get_lineas(cr, uid, context);
        
        res = line_obj.read(cr, uid, line_ids, ["id", "name"])
        res = [ ( r["id"], r["name"][:30] ) for r in res ]
        
        return res    
   
    def action_save_mrp(self, cr, uid, ids, context=None):
        
        vals = {}
        sale_id = None
        bom_obj = self.pool.get("mrp.bom")
        mrp_object =  self.pool.get("mrp.production")
        sale_line_object =  self.pool.get("sale.order.line")
        wizard = self.browse(cr, uid, ids[0], context=context)
        
        if context is not None:
            sale_id =  context["sale_id"]
            sale = self.pool.get("sale.order").browse(cr, uid, sale_id, context=context)            
            vals["origin"] = sale.name       
        
        sale_line_id = wizard.productos_line
#         sale_line = sale_line_object.read(cr, uid, sale_line_id, ["product_id", "name", "product_uom", "product_uom_qty"], context=context)[0]
        sale_line = sale_line_object.browse(cr, uid, int(sale_line_id), context=context)
        
        vals["name"] = wizard.name 
        vals["product_id"] = sale_line.product_id.id#["product_id"][0]
        vals["product_uom"] = sale_line.product_uom.id#["product_uom"][0]
        vals["product_qty"] = wizard.product_qty  
        
        if wizard.bom_id.id:
            vals["bom_id"] = wizard.bom_id.id
        else:
            valores = {
                "product_id" : vals["product_id"],
                "product_uom" : vals["product_uom"],
                "product_qty" : vals["product_qty"],
                "name" : sale_line.name#["name"],
            }            
            
            vals["bom_id"] = bom_obj.create(cr, uid, valores, context=context)                        
        
        mrp_id = mrp_object.create(cr, uid, vals, context=context)
        
        if sale_id:
            bom_ids = bom_obj.search(cr, uid, [("venta_wzrd","=",ids[0])], context=context)
            
            for id in bom_ids:
                bom_obj.write(cr, uid, id, {"bom_id": vals["bom_id"]})
          
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordenes de Fabricacion',
            'view_type': 'form',
            'view_mode': 'form,tree',            
            'res_model': 'mrp.production',   
            'res_id': mrp_id,
        }
    
    _columns = {
        "name" : fields.char('Referencia', size=64, required=True),
        "desc" : fields.char('Descripcion', readonly=True),
        "productos_line" : fields.selection(get_productos, "Producto", size=32, select=True, required=True),
        "product_id" : fields.many2one("product.product", "Producto"),
        "bom_id" : fields.many2one("mrp.bom", "Lista de Material"),
        "product_qty": fields.float('Cantidad', required=True),
        "product_uom": fields.many2one('product.uom', 'Unidad de Medida', readonly=True),
        "origin" : fields.char("Origen"),
        "bom_lines" : fields.one2many("mrp.bom", "bom_id"),
        "tipo_ldm" : fields.many2one("mrp.bom.types", "Tipo de Lista"),
    }
    
    _defaults = {  
        'name': lambda x, y, z, c: x.pool.get('ir.sequence').get(y, z, 'mrp.production') or '/',  
    }
    
mc_mrp_wizard()