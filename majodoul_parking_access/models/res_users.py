from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    maj_client_id = fields.Many2one("maj.client", string="AWTAD Client")
