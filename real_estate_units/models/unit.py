from odoo import fields, models


class RealEstateUnit(models.Model):
    _name = "real.estate.unit"
    _description = "Real Estate Unit"

    name = fields.Char(required=True)
    project_id = fields.Many2one("real.estate.project", required=True)
    unit_type = fields.Selection([("apartment", "Apartment"), ("villa", "Villa"), ("office", "Office"), ("shop", "Shop")], required=True)
    area = fields.Float(required=True)
    cost = fields.Monetary(required=True)
    target_price = fields.Monetary(required=True)
    currency_id = fields.Many2one(related="project_id.currency_id")
    status = fields.Selection([("available", "Available"), ("reserved", "Reserved"), ("sold", "Sold"), ("rented", "Rented")], default="available", tracking=True)
