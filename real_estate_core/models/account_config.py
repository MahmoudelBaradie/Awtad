from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RealEstateAccountConfig(models.Model):
    _name = "real.estate.account.config"
    _description = "Real Estate Accounting Configuration"
    _rec_name = "company_id"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    journal_id = fields.Many2one("account.journal", required=True, domain="[('type', 'in', ['general', 'purchase', 'sale'])]")

    land_asset_account_id = fields.Many2one("account.account", required=True)
    wip_account_id = fields.Many2one("account.account", required=True)
    inventory_account_id = fields.Many2one("account.account", required=True)
    investment_property_account_id = fields.Many2one("account.account", required=True)
    cost_of_sales_account_id = fields.Many2one("account.account", required=True)
    sales_revenue_account_id = fields.Many2one("account.account", required=True)
    rental_revenue_account_id = fields.Many2one("account.account", required=True)
    security_deposit_account_id = fields.Many2one("account.account", required=True)
    retention_payable_account_id = fields.Many2one("account.account", required=True)

    _sql_constraints = [
        ("company_unique", "unique(company_id)", "Only one Real Estate configuration per company is allowed."),
    ]

    @api.model
    def get_company_config(self, company=None):
        company = company or self.env.company
        config = self.search([("company_id", "=", company.id)], limit=1)
        if not config:
            raise ValidationError("Please configure Real Estate Accounting accounts first.")
        return config
