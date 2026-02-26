from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MajParking(models.Model):
    _name = "maj.parking"
    _description = "Parking Permit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(required=True, copy=False, readonly=True, default="New", tracking=True)
    access_card_id = fields.Many2one("maj.access.card", required=True, ondelete="restrict", tracking=True)
    client_id = fields.Many2one("maj.client", related="access_card_id.client_id", store=True, readonly=True)
    unit_id = fields.Many2one("maj.unit", related="access_card_id.unit_id", store=True, readonly=True)

    car_plate_en = fields.Char()
    car_plate_ar = fields.Char()
    car_color = fields.Char()
    car_model = fields.Char()
    car_type = fields.Char()
    vehicle_brand = fields.Char()
    tag_number = fields.Char()

    parking_type = fields.Selection(
        [("normal", "Normal"), ("vip", "VIP"), ("temporary", "Temporary")],
        default="normal",
        required=True,
        tracking=True,
    )
    time_in = fields.Datetime()
    time_out = fields.Datetime()
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("expired", "Expired"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = seq.next_by_code("maj.parking") or "New"
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
        return result

    @api.constrains("access_card_id")
    def _check_access_card_must_be_active(self):
        for record in self:
            if record.access_card_id and record.access_card_id.state != "active":
                raise ValidationError("Parking permit requires an active access card.")

    @api.constrains("state", "unit_id")
    def _check_floor_active_slot_limit(self):
        for record in self.filtered(lambda r: r.state == "active" and r.unit_id):
            unit = record.unit_id
            count = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("unit_id", "=", unit.id),
                    ("state", "=", "active"),
                ]
            )
            if count >= unit.max_parking_slots:
                raise ValidationError(
                    "Parking limit reached for floor %(floor)s. Max slots: %(max)s."
                    % {"floor": unit.display_name, "max": unit.max_parking_slots}
                )

    @api.constrains("time_in", "time_out")
    def _check_time_in_out(self):
        for record in self:
            if record.time_in and record.time_out and record.time_in > record.time_out:
                raise ValidationError("Time out must be after time in.")

    @api.onchange("access_card_id")
    def _onchange_access_card_id(self):
        if self.access_card_id and self.access_card_id.state != "active":
            return {
                "warning": {
                    "title": "Inactive Access Card",
                    "message": "Selected access card is not active. Parking permit will be blocked on save.",
                }
            }
        return {}

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

    def action_set_active(self):
        self.write({"state": "active"})

    def action_set_expired(self):
        self.write({"state": "expired"})

    def action_set_cancelled(self):
        self.write({"state": "cancelled"})

    def action_reset_draft(self):
        self.write({"state": "draft"})

    def action_check_in(self):
        self.write({"time_in": fields.Datetime.now()})

    def action_check_out(self):
        self.write({"time_out": fields.Datetime.now()})
