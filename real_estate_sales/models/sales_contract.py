from odoo import fields, models


class RealEstateSalesContract(models.Model):
    _name = "real.estate.sales.contract"
    _description = "Unit Sales Contract"
    _inherit = "real.estate.accounting.mixin"

    name = fields.Char(required=True)
    unit_id = fields.Many2one("real.estate.unit", required=True)
    partner_id = fields.Many2one("res.partner", required=True)
    contract_date = fields.Date(default=fields.Date.context_today)
    amount_total = fields.Monetary(required=True)
    revenue_policy = fields.Selection([("contract", "On Contract"), ("delivery", "On Delivery")], default="contract")
    delivery_status = fields.Selection([("pending", "Pending"), ("delivered", "Delivered")], default="pending")
    cost_amount = fields.Monetary(related="unit_id.cost")
    margin = fields.Monetary(compute="_compute_margin")
    currency_id = fields.Many2one(related="unit_id.currency_id")
    company_id = fields.Many2one(related="unit_id.project_id.company_id")
    state = fields.Selection([("draft", "Draft"), ("reserved", "Reserved"), ("confirmed", "Confirmed")], default="draft")

    def _compute_margin(self):
        for rec in self:
            rec.margin = rec.amount_total - rec.cost_amount

    def action_reserve(self):
        self.unit_id.status = "reserved"
        self.state = "reserved"

    def action_confirm(self):
        for rec in self:
            config = self.env["real.estate.account.config"].get_company_config(rec.company_id)
            if rec.revenue_policy == "contract" or rec.delivery_status == "delivered":
                rec._create_move(
                    ref=f"Sales Contract {rec.name}",
                    date=rec.contract_date,
                    analytic_account=rec.unit_id.project_id.analytic_account_id,
                    partner=rec.partner_id,
                    lines=[
                        {"name": rec.name, "account_id": rec.partner_id.property_account_receivable_id, "debit": rec.amount_total, "analytic": False},
                        {"name": rec.name, "account_id": config.sales_revenue_account_id, "credit": rec.amount_total},
                    ],
                )
                rec._create_move(
                    ref=f"COGS {rec.name}",
                    date=rec.contract_date,
                    analytic_account=rec.unit_id.project_id.analytic_account_id,
                    lines=[
                        {"name": rec.name, "account_id": config.cost_of_sales_account_id, "debit": rec.cost_amount},
                        {"name": rec.name, "account_id": config.inventory_account_id, "credit": rec.cost_amount},
                    ],
                )
            rec.unit_id.status = "sold"
            rec.state = "confirmed"
