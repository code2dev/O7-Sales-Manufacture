# -*- coding: utf-8 -*-
{
    'name': 'Personalizacion del Modulo de Produccion',
    'version': '1.0.0',
    'category': 'MRP',
    'sequence': 3,
    'author': 'c2d',
    'website': '',
    'summary': "",
    'description': "",
    'depends': ["sale", "mrp", "stock"],
    'data': [        
        'security/ir.model.access.csv',
        'wizard/mrp_wizard_view.xml',
        'mrp_view.xml',
        'sale_view.xml',                
    ],    
    'installable': True,
    'application': False,
    'auto_install': False,
}