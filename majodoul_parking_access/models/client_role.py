from odoo import fields, models


class MajClientRole(models.Model):
    _name = "maj.client.role"
    _description = "Client Role"

    name = fields.Char(required=True)
    description = fields.Text()


class MajClientRoleAssignment(models.Model):
    _name = "maj.client.role.assignment"
    _description = "Client Role Assignment"

    client_id = fields.Many2one("maj.client", required=True, ondelete="cascade")
    role_id = fields.Many2one("maj.client.role", required=True, ondelete="restrict")
    responsible_name = fields.Char(required=True)
    responsible_email = fields.Char()
    responsible_mobile = fields.Char()
