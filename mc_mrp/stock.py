from openerp.osv import osv, fields

class mc_stock_move(osv.osv):
    
    _inherit = 'stock.move'
    
    _columns = {
        "product_cost" : fields.float("Costo", digits=(12,2)),
        "product_cost_total" : fields.float("Total", digits=(12,2))
    }
    
    
mc_stock_move()