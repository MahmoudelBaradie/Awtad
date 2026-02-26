{
    "name": "Real Estate Core",
    "version": "18.0.1.0.0",
    "summary": "Shared master data and accounting setup for Real Estate ERP",
    "category": "Real Estate",
    "license": "LGPL-3",
    "depends": ["base", "mail", "analytic", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_config_views.xml",
        "views/menu.xml"
    ],
    "installable": True,
}
