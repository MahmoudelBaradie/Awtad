from odoo import models


class RealEstateAccountingMixin(models.AbstractModel):
    _name = "real.estate.accounting.mixin"
    _description = "Accounting Entry Helper"

    def _create_move(self, ref, date, lines, analytic_account=None, partner=None):
        self.ensure_one()
        config = self.env["real.estate.account.config"].get_company_config(self.company_id)
        move_lines = []
        for line in lines:
            vals = {
                "name": line["name"],
                "account_id": line["account_id"].id,
                "debit": line.get("debit", 0.0),
                "credit": line.get("credit", 0.0),
                "partner_id": partner.id if partner else False,
            }
            if analytic_account and line.get("analytic", True):
                vals["analytic_distribution"] = {analytic_account.id: 100}
            move_lines.append((0, 0, vals))

        move = self.env["account.move"].create({
            "journal_id": config.journal_id.id,
            "date": date,
            "ref": ref,
            "line_ids": move_lines,
        })
        move.action_post()
        return move
