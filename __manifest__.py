# -*- coding: utf-8 -*-
{
    'name': "rider",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
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
