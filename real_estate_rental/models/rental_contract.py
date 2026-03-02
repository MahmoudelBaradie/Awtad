from dateutil.relativedelta import relativedelta
from odoo import fields, models


class RealEstateRentalContract(models.Model):
    _name = "real.estate.rental.contract"
    _description = "Rental Contract"
    _inherit = "real.estate.accounting.mixin"

    name = fields.Char(required=True)
    unit_id = fields.Many2one("real.estate.unit", required=True)
    tenant_id = fields.Many2one("res.partner", required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    rent_amount = fields.Monetary(required=True)
    billing_cycle = fields.Selection([("monthly", "Monthly"), ("quarterly", "Quarterly")], default="monthly")
    security_deposit = fields.Monetary(default=0.0)
    next_invoice_date = fields.Date()
    currency_id = fields.Many2one(related="unit_id.currency_id")
    company_id = fields.Many2one(related="unit_id.project_id.company_id")
    state = fields.Selection([("draft", "Draft"), ("running", "Running"), ("closed", "Closed")], default="draft")

    def action_start(self):
        for rec in self:
            rec.unit_id.status = "rented"
            rec.next_invoice_date = rec.date_start
            rec.state = "running"
            if rec.security_deposit:
                config = self.env["real.estate.account.config"].get_company_config(rec.company_id)
                rec._create_move(
                    ref=f"Security Deposit {rec.name}",
                    date=rec.date_start,
                    partner=rec.tenant_id,
                    lines=[
                        {"name": rec.name, "account_id": rec.tenant_id.property_account_receivable_id, "debit": rec.security_deposit, "analytic": False},
                        {"name": rec.name, "account_id": config.security_deposit_account_id, "credit": rec.security_deposit, "analytic": False},
                    ],
                )

    def _cycle_delta(self):
        return relativedelta(months=1) if self.billing_cycle == "monthly" else relativedelta(months=3)

    def action_generate_rent_invoice(self):
        for rec in self.filtered(lambda c: c.state == "running" and c.next_invoice_date and c.next_invoice_date <= fields.Date.today()):
            move = self.env["account.move"].create({
                "move_type": "out_invoice",
                "partner_id": rec.tenant_id.id,
                "invoice_date": rec.next_invoice_date,
                "invoice_line_ids": [(0, 0, {
                    "name": f"Rent {rec.unit_id.name}",
                    "quantity": 1,
                    "price_unit": rec.rent_amount,
                    "account_id": self.env["real.estate.account.config"].get_company_config(rec.company_id).rental_revenue_account_id.id,
                    "analytic_distribution": {rec.unit_id.project_id.analytic_account_id.id: 100},
                })],
            })
            move.action_post()
            rec.next_invoice_date = rec.next_invoice_date + rec._cycle_delta()
