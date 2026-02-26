from odoo import fields, models


class MajClient(models.Model):
    _name = "maj.client"
    _description = "Tenant Client"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code"

    code = fields.Char(required=True, tracking=True)
    name = fields.Char(required=True, tracking=True)
    unit_ids = fields.Many2many("maj.unit", string="Units / Floors")
    contact_name = fields.Char()
    contact_email = fields.Char()
    contact_mobile = fields.Char()
    active = fields.Boolean(default=True)

    access_card_ids = fields.One2many("maj.access.card", "client_id")
    parking_ids = fields.One2many("maj.parking", "client_id")

    _sql_constraints = [
        ("maj_client_code_uniq", "unique(code)", "Client code must be unique."),
    ]
