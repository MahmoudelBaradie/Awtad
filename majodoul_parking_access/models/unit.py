from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MajUnit(models.Model):
    _name = "maj.unit"
    _description = "Unit / Floor"
    _order = "floor_number, name"

    name = fields.Char(required=True)
    floor_number = fields.Integer(required=True)
    max_parking_slots = fields.Integer(default=1, required=True)

    _sql_constraints = [
        ("max_parking_slots_positive", "CHECK(max_parking_slots > 0)", "Maximum parking slots must be greater than 0."),
    ]

    @api.constrains("floor_number")
    def _check_floor_number(self):
        for record in self:
            if record.floor_number < 0:
                raise ValidationError("Floor number cannot be negative.")
