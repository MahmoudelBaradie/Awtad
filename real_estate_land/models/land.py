from odoo import api, fields, models
from odoo.exceptions import UserError


class RealEstateLand(models.Model):
    _name = "real.estate.land"
    _description = "Land Acquisition"
    _inherit = ["mail.thread", "real.estate.accounting.mixin"]

    name = fields.Char(default="New", copy=False)
    location = fields.Char(required=True)
    area = fields.Float(required=True)
    area_uom = fields.Selection([("feddan", "Feddan"), ("qirat", "Qirat"), ("sqm", "Square Meter")], default="sqm", required=True)
    area_sqm = fields.Float(compute="_compute_area_sqm", store=True)
    purchase_price = fields.Monetary(required=True)
    additional_cost = fields.Monetary()
    total_land_cost = fields.Monetary(compute="_compute_total", store=True)
    payment_account_id = fields.Many2one("account.account", required=True)
    date = fields.Date(default=fields.Date.context_today)
    analytic_account_id = fields.Many2one("account.analytic.account", readonly=True)
    move_id = fields.Many2one("account.move", readonly=True)
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)
    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed"), ("capitalized", "Capitalized")], default="draft", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = seq.next_by_code("real.estate.land") or "New"
        records = super().create(vals_list)
        for rec in records:
            rec.analytic_account_id = self.env["account.analytic.account"].create({"name": rec.name, "company_id": rec.company_id.id}).id
        return records

    @api.depends("area", "area_uom")
    def _compute_area_sqm(self):
        for rec in self:
            if rec.area_uom == "feddan":
                rec.area_sqm = rec.area * 4200
            elif rec.area_uom == "qirat":
                rec.area_sqm = rec.area * 175
            else:
                rec.area_sqm = rec.area

    @api.depends("purchase_price", "additional_cost")
    def _compute_total(self):
        for rec in self:
            rec.total_land_cost = rec.purchase_price + rec.additional_cost

    def action_confirm(self):
        for rec in self:
            config = self.env["real.estate.account.config"].get_company_config(rec.company_id)
            rec.move_id = rec._create_move(
                ref=f"Land Acquisition {rec.name}",
                date=rec.date,
                analytic_account=rec.analytic_account_id,
                lines=[
                    {"name": rec.name, "account_id": config.land_asset_account_id, "debit": rec.total_land_cost},
                    {"name": rec.name, "account_id": rec.payment_account_id, "credit": rec.total_land_cost, "analytic": False},
                ],
            )
            rec.state = "confirmed"

    def action_capitalize(self):
        self.write({"state": "capitalized"})

    def write(self, vals):
        if any(rec.state == "capitalized" for rec in self):
            forbidden = set(vals).difference({"message_follower_ids", "activity_ids"})
            if forbidden:
                raise UserError("Capitalized land records cannot be edited.")
        return super().write(vals)
