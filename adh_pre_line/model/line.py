from odoo import api, fields, models, _
from odoo.exceptions import UserError

class adhimix_pre_line(models.Model):
	_name = 'adhimix.pre.line'

	name = fields.Char(string="Nama Line", readonly=True)
	satuan_barang = fields.Many2one(comodel_name="product.uom", required=True, string="Satuan Barang")
	kapasitas_line = fields.Float(string="Kapasitas Line", required=True)
	dibuat_oleh = fields.Many2one(comodel_name="res.users", readonly=True, string="Dibuat Oleh", default=lambda self: self._uid)
	produksi_berjalan = fields.One2many(comodel_name="adhimix.pre.line.active", inverse_name="reference", string="Produksi Berjalan")
	produksi_selesai = fields.One2many(comodel_name="adhimix.pre.line.done", inverse_name="reference", string="Produksi Selesai")
	kapasitas_terisi = fields.Float(string="Kapasitas Terisi", compute="_get_kapasitas_terisi")
	kapasitas_sisa = fields.Float(string="Kapasitas Sisa", compute="_get_kapasitas_sisa")

	# Sequence
	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('adhimix.pre.line')
		
		return super(adhimix_pre_line, self).create(vals)

	@api.depends('kapasitas_terisi')
	def _get_kapasitas_terisi(self):
		kapasitas_terisi = 0
		for rec in self:
			for x in rec.produksi_berjalan:        
				kapasitas_terisi += x.qty_produksi
			rec.kapasitas_terisi = kapasitas_terisi

	@api.depends('kapasitas_sisa')
	def _get_kapasitas_sisa(self):
		kapasitas_sisa = 0
		for rec in self:
			rec.kapasitas_sisa = rec.kapasitas_line - rec.kapasitas_terisi


class adhimix_pre_line_active(models.Model):
	_name = 'adhimix.pre.line.active'

	reference = fields.Many2one(comodel_name="adhimix.pre.line", required=True, string="Line ID")
	nomor_mo = fields.Many2one(comodel_name="mrp.production", required=True, string="Nomor MO")
	qty_produksi = fields.Float(string="Qty Produksi", required=True)
	tanggal_produksi = fields.Date(string="Tanggal Produksi")
	status_produksi = fields.Char(string="Status Produksi", compute="_get_status_produksi")

	@api.depends('status_produksi')
	def _get_status_produksi(self):
		for rec in self:
			rec.status_produksi = rec.nomor_mo.state


class adhimix_pre_line_done(models.Model):
	_name = 'adhimix.pre.line.done'

	reference = fields.Many2one(comodel_name="adhimix.pre.line", required=True, string="Line ID")
	nomor_mo = fields.Many2one(comodel_name="mrp.production", required=True, string="Nomor MO")
	qty_produksi = fields.Float(string="Qty Produksi", required=True)
	tanggal_produksi = fields.Date(string="Tanggal Produksi")
	status_produksi = fields.Char(string="Status Produksi", compute="_get_status_produksi")

	@api.depends('status_produksi')
	def _get_status_produksi(self):
		for rec in self:
			rec.status_produksi = rec.nomor_mo.state


class mrp_production(models.Model):
	_inherit = 'mrp.production'

	line_produksi = fields.Many2one(comodel_name="adhimix.pre.line", required=True, string="Line Produksi")

	# Inherit Function
	@api.model
	def create(self, values):
		if values['product_qty'] < self.env['adhimix.pre.line'].browse(values['line_produksi']).kapasitas_sisa:
			if values['product_uom_id'] == self.env['adhimix.pre.line'].browse(values['line_produksi']).satuan_barang.id:

				production = super(mrp_production, self).create(values)				
				self.env["adhimix.pre.line.active"].create({
															'reference': production.line_produksi.id,
															'nomor_mo' : production.id,
															'qty_produksi' : production.product_qty,
															'tanggal_produksi' : production.date_planned_start,
															'status_produksi' : production.state
															}).id
			else :
				raise UserError(_('Satuan Uom harus sama dengan satuan line'))					
		else :
			raise UserError(_('Kapasitas sisa line tidak mencukupi'))
		return production


	@api.multi
	def button_mark_done(self):
		super(mrp_production, self).button_mark_done()
		for production in self:
			self.env["adhimix.pre.line.done"].create({
													'reference': production.line_produksi.id,
													'nomor_mo' : production.id,
													'qty_produksi' : production.product_qty,
													'tanggal_produksi' : production.date_planned_start,
													'status_produksi' : production.state
													}).id

			active_mo = self.env['adhimix.pre.line.active'].search([('nomor_mo','=',production.id), ('reference','=',production.line_produksi.id)])
			if active_mo:
				active_mo.unlink()
