{
    'name': 'SendTrack REST API',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'summary': 'REST API for authentication, contacts, shipments and tickets',
    'depends': ['base', 'contacts', 'sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/shipment_views.xml',
        'views/ticket_views.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['pyjwt'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
