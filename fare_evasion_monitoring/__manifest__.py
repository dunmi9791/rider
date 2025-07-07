# -*- coding: utf-8 -*-
{
    'name': "Fare Evasion Monitoring",

    'summary': """
        Monitors fare evasion on public transport vehicles by analyzing passenger count data
        and transport card system data. Calculates revenue loss and detects evasion spikes.""",

    'description': """
        This module aims to:
        1. Estimate passengers without valid transport cards.
        2. Calculate estimated daily revenue loss per vehicle.
        3. Detect and alert on significant spikes in fare evasion.
        4. Provide a configurable and performant system.
        5. Support dashboard visualizations for revenue loss.

        It processes data from 'bus.log' (total passengers) and 'transport.trip' (carded passengers)
        models, introducing new models for daily loss logs and configuration.
    """,

    'author': "AI Software Engineer (Jules)",
    'website': "Not Applicable",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Operations/Fleet',
    'version': '16.0.1.0.0', # Odoo 16, version 1.0.0

    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet', 'mail', 'board'],

    # always loaded
    'data': [
        # Security
        'security/fare_evasion_groups.xml',
        'security/ir.model.access.csv',
        # Data
        'data/ir_sequence_data.xml',
        'data/cron_data.xml',
        'data/dashboard_actions.xml',
        # Views
        'views/res_config_settings_views.xml',
        'views/vehicle_revenue_loss_log_views.xml',
        'views/fleet_vehicle_views.xml',
        # 'report/dashboard_views.xml', # If custom views for dashboards are needed (board.board definitions)
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'application': True, # This module is a standalone application
    'auto_install': False,
    'license': 'LGPL-3', # Or appropriate license
}
