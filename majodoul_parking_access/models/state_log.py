from odoo import fields, models


class MajStateLog(models.Model):
    _name = "maj.state.log"
    _description = "State Transition Audit Log"
    _order = "changed_on desc"

    model_name = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)
    record_display_name = fields.Char(required=True)
    previous_state = fields.Char(required=True)
    new_state = fields.Char(required=True)
    changed_on = fields.Datetime(default=fields.Datetime.now, required=True)
    changed_by = fields.Many2one("res.users", default=lambda self: self.env.user, required=True)
