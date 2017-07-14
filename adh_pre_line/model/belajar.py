from odoo import api, fields, models, _

class Belajar(models.Model):
	_inherit = "mrp.production"

	name = fields.Char("Tes")

	@api.model
	def create(self, vals):
		if self.name :
			self.name='osaaaaaaaaaaaaaas'
		return super(Belajar, self).create(vals)