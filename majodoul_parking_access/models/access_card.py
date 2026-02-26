from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MajAccessCard(models.Model):
    _name = "maj.access.card"
    _description = "Employee Access Card"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(required=True, tracking=True)
    card_code = fields.Char(required=True, copy=False, readonly=True, default="New", tracking=True)
    card_number = fields.Char()
    card_level = fields.Char()

    employee_name = fields.Char(required=True, tracking=True)
    employee_mobile = fields.Char()
    employee_email = fields.Char()
    employee_internal_no = fields.Char()

    client_id = fields.Many2one("maj.client", required=True, ondelete="restrict", tracking=True)
    unit_id = fields.Many2one("maj.unit", required=True, ondelete="restrict", tracking=True)

    request_date = fields.Date(default=fields.Date.context_today)
    issued_date = fields.Date()
    expiry_date = fields.Date()
    received_date = fields.Date()

    state = fields.Selection(
        [("draft", "Draft"), ("issued", "Issued"), ("active", "Active"), ("expired", "Expired"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )

    parking_ids = fields.One2many("maj.parking", "access_card_id")

    _sql_constraints = [
        ("maj_access_card_code_uniq", "unique(card_code)", "Card code must be unique."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("card_code", "New") == "New":
                vals["card_code"] = seq.next_by_code("maj.access.card") or "New"
        records = super().create(vals_list)
        for rec in records:
            rec._log_state_change(False, rec.state)
        return records

    def write(self, vals):
        previous_states = {rec.id: rec.state for rec in self}
        result = super().write(vals)
        if "state" in vals:
            for rec in self:
                if previous_states.get(rec.id) != rec.state:
                    rec._log_state_change(previous_states.get(rec.id), rec.state)
                    if rec.state in ("expired", "cancelled"):
                        rec.parking_ids.filtered(lambda p: p.state != "cancelled").write({"state": "cancelled"})
        return result

    @api.constrains("client_id", "unit_id")
    def _check_client_has_unit(self):
        for record in self:
            if record.unit_id and record.client_id and record.unit_id not in record.client_id.unit_ids:
                raise ValidationError("Selected unit must be assigned to the selected client.")

    @api.constrains("issued_date", "expiry_date")
    def _check_issued_before_expiry(self):
        for record in self:
            if record.issued_date and record.expiry_date and record.issued_date > record.expiry_date:
                raise ValidationError("Issued date must be before expiry date.")

    @api.onchange("client_id")
    def _onchange_client_id(self):
        if self.client_id and self.unit_id and self.unit_id not in self.client_id.unit_ids:
            self.unit_id = False
        return {"domain": {"unit_id": [("id", "in", self.client_id.unit_ids.ids)]}}

    def _log_state_change(self, previous_state, new_state):
        self.env["maj.state.log"].sudo().create(
            {
                "model_name": self._name,
                "res_id": self.id,
                "record_display_name": self.display_name,
                "previous_state": previous_state or "",
                "new_state": new_state,
            }
        )

    def action_set_issued(self):
        self.write({"state": "issued", "issued_date": fields.Date.context_today(self)})

    def action_set_active(self):
        self.write({"state": "active"})

    def action_set_expired(self):
        self.write({"state": "expired"})

    def action_set_cancelled(self):
        self.write({"state": "cancelled"})

    def action_reset_draft(self):
        self.write({"state": "draft"})
