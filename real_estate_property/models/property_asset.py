from odoo import fields, models


class RealEstatePropertyAsset(models.Model):
    _name = "real.estate.property.asset"
    _description = "Investment Property Asset"
    _inherit = "real.estate.accounting.mixin"

    name = fields.Char(required=True)
    unit_id = fields.Many2one("real.estate.unit", required=True)
    acquisition_value = fields.Monetary(required=True)
    residual_value = fields.Monetary(default=0.0)
    useful_life_years = fields.Integer(default=20)
    depreciation_per_period = fields.Monetary(compute="_compute_depreciation")
    currency_id = fields.Many2one(related="unit_id.currency_id")
    company_id = fields.Many2one(related="unit_id.project_id.company_id")

    def _compute_depreciation(self):
        for rec in self:
            rec.depreciation_per_period = (rec.acquisition_value - rec.residual_value) / max(rec.useful_life_years * 12, 1)

    def action_post_monthly_depreciation(self):
        for rec in self:
            config = self.env["real.estate.account.config"].get_company_config(rec.company_id)
            rec._create_move(
                ref=f"Depreciation {rec.name}",
                date=fields.Date.context_today(self),
                analytic_account=rec.unit_id.project_id.analytic_account_id,
                lines=[
                    {"name": rec.name, "account_id": config.cost_of_sales_account_id, "debit": rec.depreciation_per_period},
                    {"name": rec.name, "account_id": config.investment_property_account_id, "credit": rec.depreciation_per_period},
                ],
            )
