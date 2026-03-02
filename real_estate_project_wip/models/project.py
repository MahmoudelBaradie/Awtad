from odoo import api, fields, models


class RealEstateProject(models.Model):
    _name = "real.estate.project"
    _description = "Real Estate Development Project"
    _inherit = ["mail.thread", "real.estate.accounting.mixin"]

    name = fields.Char(required=True)
    land_id = fields.Many2one("real.estate.land", required=True)
    analytic_account_id = fields.Many2one("account.analytic.account", readonly=True)
    estimated_budget = fields.Monetary(required=True)
    actual_cost = fields.Monetary(compute="_compute_actual", store=True)
    variance = fields.Monetary(compute="_compute_variance", store=True)
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)
    cost_line_ids = fields.One2many("real.estate.project.cost", "project_id")
    state = fields.Selection([("draft", "Draft"), ("running", "Running"), ("closed", "Closed")], default="draft")
    conversion_type = fields.Selection([("sale", "Inventory Units (For Sale)"), ("rent", "Investment Property (For Rent)")])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.analytic_account_id = self.env["account.analytic.account"].create({"name": rec.name, "company_id": rec.company_id.id}).id
        return records

    @api.depends("cost_line_ids.amount")
    def _compute_actual(self):
        for rec in self:
            rec.actual_cost = sum(rec.cost_line_ids.mapped("amount"))

    @api.depends("estimated_budget", "actual_cost")
    def _compute_variance(self):
        for rec in self:
            rec.variance = rec.estimated_budget - rec.actual_cost

    def action_start(self):
        self.write({"state": "running"})

    def action_close_project(self):
        for rec in self:
            if not rec.conversion_type:
                continue
            config = self.env["real.estate.account.config"].get_company_config(rec.company_id)
            target = config.inventory_account_id if rec.conversion_type == "sale" else config.investment_property_account_id
            rec._create_move(
                ref=f"Project closing {rec.name}",
                date=fields.Date.context_today(self),
                analytic_account=rec.analytic_account_id,
                lines=[
                    {"name": rec.name, "account_id": target, "debit": rec.actual_cost},
                    {"name": rec.name, "account_id": config.wip_account_id, "credit": rec.actual_cost},
                ],
            )
            rec.state = "closed"


class RealEstateProjectCost(models.Model):
    _name = "real.estate.project.cost"
    _description = "Project Actual Cost"

    project_id = fields.Many2one("real.estate.project", required=True, ondelete="cascade")
    date = fields.Date(default=fields.Date.context_today)
    category = fields.Selection([
        ("foundations", "Foundations"), ("concrete", "Concrete"), ("steel", "Steel"), ("finishing", "Finishing"),
        ("marble", "Marble"), ("equipment", "Equipment"), ("consultancy", "Consultancy"), ("other", "Other")
    ], required=True)
    description = fields.Char(required=True)
    amount = fields.Monetary(required=True)
    vendor_id = fields.Many2one("res.partner")
    currency_id = fields.Many2one(related="project_id.currency_id")

    def action_post_cost_entry(self):
        for line in self:
            config = self.env["real.estate.account.config"].get_company_config(line.project_id.company_id)
            line.project_id._create_move(
                ref=f"Project Cost {line.project_id.name}",
                date=line.date,
                analytic_account=line.project_id.analytic_account_id,
                partner=line.vendor_id,
                lines=[
                    {"name": line.description, "account_id": config.wip_account_id, "debit": line.amount},
                    {"name": line.description, "account_id": line.vendor_id.property_account_payable_id or config.retention_payable_account_id, "credit": line.amount, "analytic": False},
                ],
            )
