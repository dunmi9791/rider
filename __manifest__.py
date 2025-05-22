# -*- coding: utf-8 -*-
{
    'name': "rider",

    'summary': """A comprehensive Odoo module for managing vehicle operations, including vehicle information, workshop activities (job cards, fund requests), and financial tracking (cash requisitions, expense requests).""",

    'description': """
The Rider module provides a robust solution for businesses managing a fleet of vehicles or workshop operations. Key functionalities include:
- Detailed vehicle information management (make, model, year, chassis number, registration, mileage history).
- Vehicle check-in and check-out processes.
- Workshop job card integration.
- Management of fund requests for workshop parts and services.
- Cash requisition and expense request workflows with multi-level approvals.
- Tracking of parts, expenses, and financial reconciliation.
This module integrates with core Odoo modules like Sales, Accounting, and HR to streamline operations and provide a centralized system for all vehicle-related activities.
    """,

    'author': "Secteur Network Solutions",
    'website': "http://www.secteurnetworks.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'sale_management', 'account', 'hr'],

    # always loaded
    'data': [
        'data/groups.xml',
        'wizard/reconcile.xml',
        'wizard/checkin_out.xml',
        'views/actions.xml',
        'views/views.xml',
        'views/custom.xml',
        'data/subtypes.xml',
        'views/templates.xml',
        'data/automation.xml',
        'report/report.xml',
        'report/report_template.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
