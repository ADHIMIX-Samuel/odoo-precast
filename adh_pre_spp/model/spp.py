from odoo import api, fields, models, _
from datetime import timedelta, datetime
import time


class adhimix_pre_spp(models.Model):
 	_name = 'adhimix.pre.spp'

	name = fields.Char(string="Nomor Spp", readonly=True)
	tanggal = fields.Date("Tanggal Pembuatan SPP", required=True,default=lambda self:time.strftime("%Y-%m-%d"))
	product_list = fields.One2many(comodel_name="adhimix.pre.spp.line",inverse_name="reference",string="List Barang")
	rencana_produksi = fields.One2many(comodel_name="adhimix.pre.rencana.produksi",inverse_name="reference",string="Rencana Produksi")
	rencana_pengiriman = fields.One2many(comodel_name="adhimix.pre.rencana.pengiriman",inverse_name="reference",string="Rencana Pengiriman")
	rencana_stressing = fields.One2many(comodel_name="adhimix.pre.rencana.stressing",inverse_name="reference",string="Rencana Stressing")
	rencana_install = fields.One2many(comodel_name="adhimix.pre.rencana.install",inverse_name="reference",string="Rencana Install")

	# Sequence
	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('adhimix.pre.spp')
		return super(adhimix_pre_spp, self).create(vals)

	@api.multi
	def button_simulasi(self):
		for rec in self:
			for product in rec.product_list:
				qty_produksi = product.qty
				line_ids = self.env["adhimix.pre.line"].search([('satuan_barang','=',product.satuan_barang.id)])
				if line_ids:
					for line in line_ids:
						if line.kapasitas_sisa >= qty_produksi:
							qty = qty_produksi
							qty_produksi = 0
						elif line.kapasitas_sisa < qty_produksi and line.kapasitas_sisa > 0:
							qty = line.kapasitas_sisa
							qty_produksi = qty_produksi - line.kapasitas_sisa		

						self.env["adhimix.pre.rencana.produksi"].create({
																		'reference': rec.id,
																		'product_id' : product.product_id.id,
																		'line_produksi' : line.id,																		
																		'qty' : qty
																		}).id
		# cara melooping tanggal rencana_produksi
		# 	x = 0
		# 	from_date = datetime.now()
		# 	for product in rec.product_list:
		# 		while x < product.qty:                    
		# 			self.env["adhimix.pre.rencana.produksi"].create({
		# 															'reference': rec.id,
		# 															'product_id' : product.product_id.id,
		# 															'tanggal_mulai':from_date
		# 															# 'qty' : qty
		# 															}).id
		# 			from_date = from_date + timedelta(days = 1)          
		# 			x = x + 1
		# return True
			

	@api.multi
	def button_reset(self):
		for rec in self:
			for x in rec.rencana_produksi:
				x.unlink()


class adhimix_pre_spp_line(models.Model):
	_name ="adhimix.pre.spp.line"

	reference = fields.Many2one(comodel_name="adhimix.pre.spp",string="Reference")
	product_id = fields.Many2one(comodel_name="product.product",string="Nama Barang", required=True)
	satuan_barang = fields.Many2one(comodel_name="product.uom", required=True, string="Satuan Barang" )
	qty = fields.Float(string="Qty",required=True)

	@api.onchange('product_id')
	def onchange_product_id(self):
		self.satuan_barang = self.product_id.uom_id


class adhimix_pre_rencana_produksi(models.Model):
	_name = "adhimix.pre.rencana.produksi"

	reference = fields.Many2one(comodel_name="adhimix.pre.spp",string="Reference")
	product_id = fields.Many2one(comodel_name="product.product",string="Nama Barang")
	line_produksi = fields.Many2one(comodel_name="adhimix.pre.line", string="Line Produksi")
	qty = fields.Float(string="Qty")
	tanggal_mulai = fields.Date(string="Tanggal Mulai")
	# tanggal_selesai= fields.Date(string="Tanggal Selesai")
	nomor_mo = fields.Many2one(comodel_name="mrp.production",string="Nomor MO",)
	qty_done = fields.Float(string="Qty Selesai")
	qty_cancel = fields.Float(string="Qty Batal")
	qty_remaining = fields.Float(string="Qty Sisa")
	qty_pindah = fields.Float(string="Qty Pindah")
	qty_pindahan = fields.Float(string="Qty Pindahan")
	status = fields.Selection([('Menunggu','Menunggu'),('Produksi','Produksi')], string="Status", default="Menunggu")

	@api.multi
	def button_produksi(self):
		self.status = 'Produksi'
		for rec in self:
			mo_id = self.env["mrp.production"].create({
												'product_id' : rec.product_id.id,
												'product_qty' : rec.qty,
												'line_produksi' : rec.line_produksi.id,
												'date_Planned_start' : rec.tanggal_mulai,
												'nomor_spp' : rec.reference.id,
												'product_uom_id' : rec.product_id.uom_id.id,
												'bom_id' : rec.product_id.id
												}).id
			self.nomor_mo = mo_id


class adhimix_pre_rencana_pengiriman(models.Model):
	_name = 'adhimix.pre.rencana.pengiriman'

	reference = fields.Many2one(comodel_name="adhimix.pre.spp", string="Reference")
	product_id = fields.Many2one(comodel_name="product.product", string="Nama Barang")
	qty = fields.Float(string="Qty")
	nomor_do = fields.Many2one(comodel_name="stock.picking", string="Nomor DO")
	jadwal_kirim = fields.Date(string="Jadwal Kirim")
	tanggal_kirim = fields.Date(string="Tanggal Kirim")
	qty_done = fields.Float(string="Qty Selesai")
	qty_cancel = fields.Float(string="Qty Batal")
	qty_repair = fields.Float(string="Repair")
	qty_reject = fields.Float(string="Reject")


class adhimix_pre_rencana_stressing(models.Model):
	_name = 'adhimix.pre.rencana.stressing'

	reference = fields.Many2one(comodel_name="adhimix.pre.spp", string="Reference")
	product_id = fields.Many2one(comodel_name="product.product", string="Nama Barang")
	qty = fields.Float(string="Qty")
	jadwal_stressing = fields.Date(string="Jadwal Stressing")
	tanggal_stressing = fields.Date(string="Tanggal Stressing")
	qty_done = fields.Float(string="Qty Selesai")
	qty_cancel = fields.Float(string="Qty Batal")
	qty_repair = fields.Float(string="Repair")
	qty_reject = fields.Float(string="Reject")


class adhimix_pre_rencana_install(models.Model):
	_name = 'adhimix.pre.rencana.install'

	reference = fields.Many2one(comodel_name="adhimix.pre.spp", string="Reference")
	product_id = fields.Many2one(comodel_name="product.product", string="Nama Barang")
	qty = fields.Float(string="Qty")
	jadwal_install = fields.Date(string="Jadwal Install")
	tanggal_install = fields.Date(string="Tanggal Install")
	qty_done = fields.Float(string="Qty Selesai")
	qty_cancel = fields.Float(string="Qty Batal")
	qty_repair = fields.Float(string="Repair")
	qty_reject = fields.Float(string="Reject")


class mrp_production(models.Model):
	_inherit = 'mrp.production'

	nomor_spp = fields.Many2one(comodel_name="adhimix.pre.spp", string="Nomor SPP")