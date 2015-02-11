from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import datetime
import time

class mc_mrp_tipo(osv.osv) :     
    _name = "mc.mrp.tipo"
    _desc = "Clase para definir los distintos tipos de Fabricacion"
    
    _columns = {                
        "name" : fields.char("Nombre"),
        "estados" : fields.one2many("mc.mrp.estado", "tipo", "Estados")              
    }
mc_mrp_tipo()

class mc_mrp_estado(osv.osv) :     
    _name = "mc.mrp.estado"
    _desc = "Clase para determinar los distintos estados por los que pasa un tipo de fabricacion"
    
    def create(self, cr, uid, args, context=None):
        
        name = args["name"]
        name = name[:3]
        args["code"] = name.upper()        
        
        return super(mc_mrp_estado, self).create(cr, uid, args, context=context)
    
    def write(self, cr, uid, ids, args, context=None):
        
        name = args["name"]
        name = name[:3]
        args["code"] = name.upper()        
        
        return super(mc_mrp_estado, self).write(cr, uid, ids, args, context=context)
    
    _columns = {  
        "code" : fields.char("Codigo", size=3),
        "name" : fields.char("Nombre", required=True),
        "tipo" : fields.many2one("mc.mrp.tipo", "Tipo")                
    }
mc_mrp_estado()

class mc_mrp_estado_line(osv.osv) :     
    _name = "mc.mrp.estado.line"
    _desc = "Lineas generadas por cada estado de fabricacion relacionado al tipo de fabricacion seleccionado en la orden"
        
    def calcular_fecha(self, cr, uid, context):
      
        a = datetime.datetime.now()
        x = a.strftime('%d/%m/%Y %H:%M:%S')
      
        return x
    
    def action_start_mrp(self, cr, uid, ids, context):
        
        line = self.browse(cr, uid, ids, context=context)[0]
        
        sale_obj = self.pool.get("sale.order")
        sale_id = line.order_id.id
        
        sale_row = sale_obj.read(cr, uid, [sale_id], ["mrp_sale_state"])[0]
        sale_state = sale_row["mrp_sale_state"]
        
        if sale_state == "Sin Iniciar" or sale_state == "En proceso":                           
            sale_obj.write(cr, uid, [sale_id], {"mrp_sale_state" : line.estatus_id.code})
                 
        else:
            sale_state = sale_state + "," + line.estatus_id.code            
            sale_obj.write(cr, uid, [sale_id], {"mrp_sale_state" : sale_state})
        
        date_order = self.calcular_fecha(cr, uid, context)#time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.write(cr, uid, ids, {"state":"started", "user_id" : uid, "date_start" : date_order}, context)
        
        return True 
    
    def action_stop_mrp(self, cr, uid, ids, context):
              
        line = self.browse(cr, uid, ids, context=context)[0]
        
        sale_obj = self.pool.get("sale.order")
        sale_id = line.order_id.id
        
        sale_row = sale_obj.read(cr, uid, [sale_id], ["mrp_sale_state"])[0]
        sale_state = sale_row["mrp_sale_state"]
        
        if line.estatus_id.code in sale_state:
            sale_state = sale_state.replace(line.estatus_id.code, "")           
                
        if sale_state == "":
            sale_state = "En proceso"
            
        else:
            if sale_state[0] == ",": 
                sale_state = sale_state[1:]  
                
            if sale_state[len(sale_state) - 1] == ",": 
                sale_state = sale_state[:-1]               
        
        date_order = self.calcular_fecha(cr, uid, context)#time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.write(cr, uid, ids, {"state":"done", "date_finish" : date_order}, context)
        
        lineas = self.search(cr, uid, [("order_id", "=", sale_id)], context=context)
        bnd = True
        
        for linea in lineas:
            line_browse = self.browse(cr, uid, linea, context=context)            
            
            if line_browse["state"] != "done":
                bnd = False
        
        if bnd:
            sale_state = "Finalizado"
            sale_obj.write(cr, uid, sale_id, {"mrp_sale_state" : sale_state})
            return {'type': 'ir.actions.client', 'tag': 'reload'}        
        
        return sale_obj.write(cr, uid, sale_id, {"mrp_sale_state" : sale_state})
    
    _columns = {                
        "name" : fields.char("Nombre"),
        "estatus_id" : fields.many2one("mc.mrp.estado", "Proceso"),
        "order_id" : fields.many2one("sale.order", "Venta"),
        'user_id': fields.many2one('res.users', 'Usuario', select=True),
        'date_start': fields.datetime('Fecha de Inicio', select=True),
        'date_finish': fields.datetime('Fecha de Termino', select=True),
        'state': fields.selection([
            ('new', 'Sin Iniciar'),            
            ('started', 'Iniciada'),
            ('done', 'Finalizada'),
            ('unused', 'No Realizada'),
            ], 'Produccion', select=True),                
    }
mc_mrp_estado()

class mc_sale_order(osv.osv):
    _inherit = "sale.order"
    
    _columns = {
        "estatus_line" : fields.one2many("mc.mrp.estado.line", "order_id", "Proceso"),
        'mrp_sale_type': fields.many2one("mc.mrp.tipo", "Tipo de Venta"),
        'mrp_sale_state': fields.char("Produccion"),
        'mrp_design' : fields.boolean("Diseno"),
        'no_pasadas' : fields.char("Numero de pasadas"), 
    }
    
    def action_ver_mrp(self, cr, uid, ids, context):
                
        this = self.browse(cr, uid, ids, context=context)[0]
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordenes de Fabricacion',
            'view_mode': 'tree,form',            
            'res_model': 'mrp.production',
            'domain': [("origin","=",this.name)]
            }
    
    def action_finish_mrp(self, cr, uid, ids, context=None):
        
        state_line_obj = self.pool.get("mc.mrp.estado.line")
        lineas = state_line_obj.search(cr, uid, [("order_id", "=", ids[0])], context=context)
        
        for linea in lineas:
            line_browse = state_line_obj.browse(cr, uid, linea, context=context)
            
            if line_browse["state"] == "new":
                state_line_obj.write(cr, uid, linea, {"state" : "unused"})
        
        self.write(cr, uid, ids, {"mrp_sale_state" : "Finalizado"})        
        return True    
    
    def action_reopen_mrp(self, cr, uid, ids, context=None):
        
        state_line_obj = self.pool.get("mc.mrp.estado.line")
        lineas = state_line_obj.search(cr, uid, [("order_id", "=", ids[0])], context=context)
        
        for linea in lineas:
            line_browse = state_line_obj.browse(cr, uid, linea, context=context)
            
            if line_browse["state"] == "unused":
                state_line_obj.write(cr, uid, linea, {"state" : "new"})
                
        self.write(cr, uid, ids, {"mrp_sale_state" : "En proceso"})        
        return True
        
    def action_button_confirm(self, cr, uid, ids, context=None):
        
        sale = self.browse(cr, uid, ids, context=context)[0]
        
        if not sale.estatus_line:        
            
            estado = ""
            state_obj = self.pool.get("mc.mrp.estado")
            state_line_obj = self.pool.get("mc.mrp.estado.line")            
            
            tipo = sale.mrp_sale_type.id
            states_ids = state_obj.search(cr, uid, [("tipo", "=", tipo)], context=context)
            
            for state in states_ids:
                state_row = state_obj.read(cr, uid, [state], ["code"], context=None)[0]                
                
                if estado == "":                           
                    estado = state_row["code"]                    
                else:
                    estado = estado + "," + state_row["code"]                    
                
                state_line_obj.create(cr, uid, {"estatus_id":state, "order_id":ids[0], "state":"new"})
            self.write(cr, uid, ids, {"mrp_sale_state" : "Sin Iniciar"})
            
        return super(mc_sale_order, self).action_button_confirm(cr, uid, ids, context=context)
    
    def get_default_type(self, cr, uid, ids):
        
        res = self.pool.get("mc.mrp.tipo").search(cr, uid, [])
        
        return res and res[0] or False
    
mc_sale_order()