from odoo import api, fields, models, _

class adhimix_pre_line(models.Model):
	_name = 'adhimix.pre.line'

	name = fields.Char(string="Nama Line", readonly=True)
	satuan_barang = fields.Many2one(comodel_name="product.uom", required=True, string="Satuan Barang")
	kapasitas_line = fields.Float(string="Kapasitas Line", required=True)
	dibuat_oleh = fields.Many2one(comodel_name="res.users", readonly=True, string="Dibuat Oleh", default=lambda self: self._uid)
	produksi_berjalan = fields.One2many(comodel_name="adhimix.pre.line.active", inverse_name="reference", string="Produksi Berjalan")

	# Sequence
	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('adhimix.pre.line')
		
		return super(adhimix_pre_line, self).create(vals)


class adhimix_pre_line_active(models.Model):
	_name = 'adhimix.pre.line.active'

	reference = fields.Many2one(comodel_name="adhimix.pre.line", required=True, string="Line ID")
	nomor_mo = fields.Many2one(comodel_name="mrp.production", required=True, string="Nomor MO")
	qty_produksi = fields.Float(string="Qty Produksi", required=True)
	tanggal_produksi = fields.Date(string="Tanggal Produksi")
	status_produksi = fields.Char(string="Status Produksi")


class mrp_production(models.Model):
	_inherit = 'mrp.production'

	line_produksi = fields.Many2one(comodel_name="adhimix.pre.line", required=True, string="Line Produksi")

	@api.model
	def create(self, values):
		if not values.get('name', False) or values['name'] == _('New'):
			values['name'] = self.env['ir.sequence'].next_by_code('mrp.production') or _('New')
		if not values.get('procurement_group_id'):
			values['procurement_group_id'] = self.env["procurement.group"].create({'name': values['name']}).id
		production = super(mrp_production, self).create(values)
		production._generate_moves()
		self.env["adhimix.pre.line.active"].create({
													'reference': production.line_produksi.id,
													'nomor_mo' : production.id,
													'qty_produksi' : production.product_qty,
													'tanggal_produksi' : production.date_planned_start,
													'status_produksi' : production.state
													}).id
		return production