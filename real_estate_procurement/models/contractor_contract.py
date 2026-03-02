from odoo import fields, models


class RealEstateContractorContract(models.Model):
    _name = "real.estate.contractor.contract"
    _description = "Contractor Contract"
    _inherit = "real.estate.accounting.mixin"

    name = fields.Char(required=True)
    project_id = fields.Many2one("real.estate.project", required=True)
    contractor_id = fields.Many2one("res.partner", required=True)
    contract_value = fields.Monetary(required=True)
    retention_percent = fields.Float(default=10.0)
    currency_id = fields.Many2one(related="project_id.currency_id")
    company_id = fields.Many2one(related="project_id.company_id")
    line_ids = fields.One2many("real.estate.contractor.bill", "contract_id")


class RealEstateContractorBill(models.Model):
    _name = "real.estate.contractor.bill"
    _description = "Contractor Progress Bill"

    contract_id = fields.Many2one("real.estate.contractor.contract", required=True, ondelete="cascade")
    date = fields.Date(default=fields.Date.context_today)
    amount = fields.Monetary(required=True)
    retention_amount = fields.Monetary(compute="_compute_retention", store=True)
    payable_amount = fields.Monetary(compute="_compute_retention", store=True)
    currency_id = fields.Many2one(related="contract_id.currency_id")

    def _compute_retention(self):
        for rec in self:
            rec.retention_amount = rec.amount * rec.contract_id.retention_percent / 100
            rec.payable_amount = rec.amount - rec.retention_amount

    def action_post_bill(self):
        for rec in self:
            config = self.env["real.estate.account.config"].get_company_config(rec.contract_id.company_id)
            rec.contract_id._create_move(
                ref=f"Contractor Bill {rec.contract_id.name}",
                date=rec.date,
                analytic_account=rec.contract_id.project_id.analytic_account_id,
                partner=rec.contract_id.contractor_id,
                lines=[
                    {"name": rec.contract_id.name, "account_id": config.wip_account_id, "debit": rec.amount},
                    {"name": rec.contract_id.name, "account_id": config.retention_payable_account_id, "credit": rec.retention_amount, "analytic": False},
                    {"name": rec.contract_id.name, "account_id": rec.contract_id.contractor_id.property_account_payable_id, "credit": rec.payable_amount, "analytic": False},
                ],
            )
