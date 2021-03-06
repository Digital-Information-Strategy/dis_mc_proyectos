# -*- coding: utf-8 -*-
##############################################################################
#
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import math
from openerp import netsvc
from openerp.tools.translate import _
from osv import osv, fields
from openerp.tools.safe_eval import safe_eval as eval
import openerp.addons.decimal_precision as dp
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class product_product(osv.osv):
	_inherit = 'product.product'
	_columns = {
		'name_template': fields.related('product_tmpl_id', 'name', string="Template Name", type='char', size=256, store=True, select=True),
		'default_code': fields.char('Internal Reference', size=64, select=True),
		'check_cerca': fields.boolean('Cerca'),
		'check_vertical': fields.boolean('Tubo Vertical'),
		'check_horizontal': fields.boolean('Tubo Horizontal'),
		'check_arriostre': fields.boolean('Tubo Arriostre'),
		'servicio_total': fields.boolean('Servicio Total'),
		'mano_obra': fields.boolean('Mano de obra'),
		'check_tuberia_marco': fields.boolean('Tuberia Marco'),
		'check_tuberia_diagonal': fields.boolean('Tuberia Diagonal'),
		'check_refuerzo_horizontal': fields.boolean('Refuerzo Horizontal'),
		'check_tuberia_columnas': fields.boolean('Tuberia Columnas'),
		}
	_sql_constraints = [
		('default_code_uniq', 'unique (default_code)', 'La Referencia interna del producto debe ser única!'),
	]
product_product()

class product_template(osv.osv):
	_inherit = 'product.template'
	_columns = {
		'name': fields.char('Name', size=256, required=True, translate=True, select=True),
		}
product_template()

class materials_list(osv.osv):
	_name = 'materials.list'
	_columns = {
		'name': fields.char('Nombre',required=True, unique=True),
		'active': fields.boolean('Activo'),
		#'product_id': fields.many2one('product.product','Producto',required=True),
		#'altura': fields.float('Altura'),
		'materials_lines': fields.one2many('materials.list.line','parent_id','Materiales'),
		}
	defaults = {
			'active': True,
		}

materials_list()

class materials_list_line(osv.osv):
	_name = 'materials.list.line'
	_columns = {
		'parent_id': fields.many2one('materials.list','Lista Padre', ondelete='cascade', required=True),
		'sequence': fields.integer('Secuencia', help="Secuencia en la que se muestran las lineas"),
		'product_id': fields.many2one('product.product','Producto',required=True),
		'product_uom_id': fields.many2one('product.uom','Unidad de Medida'),
		#'quantity': fields.float('Cantidad'),
		'codigo_python_cant': fields.text('Codigo Python para Cantidad', required=True, help="Campo utilizado para calcula la cantidad del producto en la lista de materiales, por medio de codigo python."),
		}
	_defaults = {
			'codigo_python_cant': 'result=0',
		}

	def onchange_product_id(self, cr, uid, ids, product_id, context=None):
		if not product_id:
			return True
		model_data=self.pool.get('product.product').browse(cr, uid, product_id, context=context)
		product_uom_id=model_data.uom_id.id
		return {'value': {'product_uom_id':float(product_uom_id)}}
materials_list_line()


class sale_order(osv.osv):
	_inherit = 'sale.order'

	def get_products(self, cr, uid, ids, materials_list_id, context=None):
		lines_obj = self.pool.get('sale.order.line')
		conditions = lines_obj.search(cr, uid, [('order_id', '=', ids[0]), ('materials_list_id','=',materials_list_id)])
		res=0
		for line in lines_obj.browse(cr, uid, conditions, context=context):
			if line.product_id and line.product_id.type=="product":
				res+=line.price_subtotal
		return res

	def get_services(self, cr, uid, ids, materials_list_id, context=None):
		lines_obj = self.pool.get('sale.order.line')
		conditions = lines_obj.search(cr, uid, [('order_id', '=', ids[0]), ('materials_list_id','=',materials_list_id)])
		res=0
		for line in lines_obj.browse(cr, uid, conditions, context=context):
			if line.product_id and line.product_id.type=="service":# and line.product_id.servicio_total==False:
				res+=line.price_subtotal
				print "RESSSSSSSSSSSSSSSSSSSSSS_: "+str(line.price_subtotal)+" "+str(line.name)
		return res

	def _amount_tpa(self, cr, uid, ids, field_name, arg, context=None):
		lines_obj = self.pool.get('sale.order.line')
		conditions = lines_obj.search(cr, uid, [('order_id', '=', ids[0])])
		res = {}
		amount=0
		res[ids[0]]=0
		if context is None:
			context = {}
		for line in lines_obj.browse(cr, uid, conditions, context=context):
			if line.product_id.type!='service':
				amount=amount+line.price_subtotal_cost
		res[ids[0]] = amount
		return res

	def _amount_tps(self, cr, uid, ids, field_name, arg, context=None):
		lines_obj = self.pool.get('sale.order.line')
		conditions = lines_obj.search(cr, uid, [('order_id', '=', ids[0])])
		res = {}
		res[ids[0]]=0
		if context is None:
			context = {}
		for line in lines_obj.browse(cr, uid, conditions, context=context):
			if line.product_id.type=='service':
				res[ids[0]] = res[ids[0]]+line.price_subtotal_cost
		return res

	def _amount_utilidad(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		if context is None:
			context = {}
		tpa = self.browse(cr, uid, ids, context=context)[0].cost_tpa
		tps = self.browse(cr, uid, ids, context=context)[0].cost_tps
		res[ids[0]]=(tpa*0.7)+(tps*0.7)
		return res

	def _amount_gravado(self, cr, uid, ids, field_name, arg, context=None):
		lines_obj = self.pool.get('sale.order.line')
		conditions = lines_obj.search(cr, uid, [('order_id', '=', ids[0])])
		res = {}
		res[ids[0]]=0
		if context is None:
			context = {}
		for line in lines_obj.browse(cr, uid, conditions, context=context):
			if line.product_id.type!='service':
				res[ids[0]] = res[ids[0]]+line.price_subtotal_cost
		return res

	def _amount_excento(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		if context is None:
			context = {}
		tps = self.browse(cr, uid, ids, context=context)[0].cost_tps
		utilidad = self.browse(cr, uid, ids, context=context)[0].cost_utilidad
		res[ids[0]] = tps+utilidad
		return res
	def _amount_cost_total(self, cr, uid, ids, field_name, arg, context=None):
		#TOTAL=Total gravado+total exento+impuesto
		res={}
		if context is None:
			context = {}
		t_gravado = self.browse(cr, uid, ids, context=context)[0].cost_total_gravado
		t_excento = self.browse(cr, uid, ids, context=context)[0].cost_total_excento
		impuesto = self.browse(cr, uid, ids, context=context)[0].amount_tax
		res[ids[0]]=t_gravado+t_excento+impuesto
		return res

	def _amount_impuesto(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = 0.0
			val = 0.0
			cur = order.pricelist_id.currency_id
			for line in order.order_line:
				val += self._amount_line_tax(cr, uid, line, context=context)
			res[order.id] = cur_obj.round(cr, uid, cur, val)
		return res

	_columns = {
		'sale_materials_list_line': fields.one2many('sale.order.materials.line','order_id','Lista de Materiales'),
		'sale_cost_list_line': fields.one2many('sale.order.line','order_id','Líneas de Costo'),
		'genera_proyecto': fields.boolean('Genera proyeto'),
		'proyecto': fields.many2one('project.project','Proyecto'),
		'codigo_python': fields.char('Codigo Python'),
		'resultado': fields.float('Cantidad'),
		'cost_tpa': fields.function(_amount_tpa, string='Total Productos Almacenables', digits_compute= dp.get_precision('Product Price')),
		'cost_tps': fields.function(_amount_tps, string='Total Productos Servicios', digits_compute= dp.get_precision('Product Price')),
		'cost_utilidad': fields.function(_amount_utilidad, string='Utilidad', digits_compute= dp.get_precision('Product Price')),
		'cost_total_gravado': fields.function(_amount_gravado, string='Total Gravado', digits_compute= dp.get_precision('Product Price')),
		'cost_total_excento': fields.function(_amount_excento, string='Total Excento', digits_compute= dp.get_precision('Product Price')),
		'cost_impuestos': fields.function(_amount_impuesto, string='Impuestos', digits_compute= dp.get_precision('Product Price')),
		'cost_total': fields.function(_amount_cost_total, string='Total', digits_compute= dp.get_precision('Product Price')),
		}
	def btn_limpiar_lineas(self, cr, uid, ids, context=None):
		print "BORRADO"
		if ids!=[]:
			bom=self.pool.get('sale.order.line')
			list_ids = bom.search(cr, uid, [('order_id', '=', ids[0])])
			bom.unlink(cr, uid, list_ids, context=None)
		return True
	#PARA LOS CAMPOS RELACIONADOS COMO EL TUBO_VERTICAL SE DEBE CREAR UN IF
	#PERO PARA LOS CAMPOS COMO CANTIDADDE METROS(FLOAT) O ARRIOSTRE(BOOLEAN) SE DEBEN MAPEAR EN LOCALDICT
	def btn_cargar(self, cr, uid, ids, context=None):
		self.btn_limpiar_lineas(cr, uid, ids, context=context)
		class BrowsableObject(object):
			def __init__(self, pool, cr, uid, dict):
				self.pool = pool
				self.cr = cr
				self.uid = uid
				self.dict = dict

			def __getattr__(self, attr):
				#print "CLASEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE: "+str(attr)
				#return
				return attr in self.dict and self.dict.__getitem__(attr) or 0.0


		#prod_objetos=self.pool.get('product.product')
		#conditions = prod_objetos.search(cr, uid, [ ])
		#prod=prod_objetos.browse(cr, uid, conditions, context=context)
		#for p in prod:
			#productos_dict[p.default_code]=p.list_price FINAL DEL FOR DE PROUCTOS

		#self.write(cr,uid,ids[0],{'resultado':localdict['result']},context)

		if context.get('sale_materials_list_line'):
			for w in context.get('sale_materials_list_line'):
				linea=model_data=self.pool.get('sale.order.materials.line').browse(cr, uid, w[1], context=context)
				#print "print: "+str(linea.materials_list_id.name)
				productos_dict={}
				cantidad_metros=linea.cantidad_metros
				separacion_vertical=linea.separacion_vertical
				separacion_arriostre=linea.separacion_arriostre
				alambre_pua=linea.alambre_pua
				alambre_navaja=linea.alambre_navaja
				altura_cerca=linea.altura_cerca
				instalado_sobre=linea.instalado_sobre
				tacos_tubo=linea.tacos_tubo
				arriostre=linea.arriostre
				cacheras=linea.cacheras
				cantidad_cacheras=linea.cantidad_cacheras
				pintura=linea.pintura
				cantidad_lineas=linea.cantidad_lineas
				tubo_horizontal=linea.tubo_horizontal
				#ADICIONALES
				ancho_porton=linea.ancho_porton
				altura_porton=linea.altura_porton
				tipo_porton=linea.tipo_porton
				tuberia_diagonal=linea.tuberia_diagonal
				cantidad_diagonales=linea.cantidad_diagonales
				refuerzo_horizontal=linea.refuerzo_horizontal
				cantidad_refuerzos_horizontales=linea.cantidad_refuerzos_horizontales
				cantidad_hojas=linea.cantidad_hojas
				tensores=linea.tensores
				for ml in linea.materials_list_id.materials_lines:
					#print "standarddddddddddddddddddddddddddddddddddddddddd: "+str(ml.product_id.standard_price)
					#######################################################
					product_obj = BrowsableObject(self.pool, cr, uid, productos_dict)
					localdict = {
								'producto': product_obj,
								'cantidad_metros': cantidad_metros,
								'altura_cerca': altura_cerca,
								'instalado_sobre': instalado_sobre,
								'tacos_tubo': tacos_tubo,
								'separacion_vertical': separacion_vertical,
								'arriostre': arriostre,
								'separacion_arriostre': separacion_arriostre,
								'cacheras': cacheras,
								'cantidad_cacheras': cantidad_cacheras,
								'alambre_navaja': alambre_navaja,
								'alambre_pua': alambre_pua,
								'pintura': pintura,
								'cantidad_lineas': cantidad_lineas,
								'tubo_horizontal': tubo_horizontal,
								'ancho_porton': ancho_porton,
								'altura_porton': altura_porton,
								'tipo_porton': tipo_porton,
								'tuberia_diagonal': tuberia_diagonal,
								'cantidad_diagonales': cantidad_diagonales,
								'refuerzo_horizontal': refuerzo_horizontal,
								'cantidad_refuerzos_horizontales': cantidad_refuerzos_horizontales,
								'cantidad_hojas': cantidad_hojas,
								'tensores': tensores,
								'result':None,
								'math': math,
								}
					#dict = {'productos':product_obj,'result': None}
					#codigo=self.browse(cr, uid, ids[0], context=context).codigo_python
					try:
						print "EVALLLLLLLLLLLLLLLLL: "+str(eval(ml.codigo_python_cant, localdict, mode='exec', nocopy=True))
					except Exception,e:
						raise osv.except_osv(('Error!'),("\n Existe un problema con el siguiente código python: "+str(ml.codigo_python_cant)+" del producto: "+str(ml.product_id.name)+"\n\nError: "+str(e)))
					#print "printTTTTTTTTTTTTTTTTTTTTTTT: "+str(localdict)
					if ml.product_id.taxes_id!=[]:
						imp_id=[(4,ml.product_id.taxes_id[0].id)]
					else:
						imp_id=[]
					#crear producto genérico con referencia interna CERCA
					if linea.cerca_id and ml.product_id.default_code=='CERCA':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print_________________________TAX: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.cerca_id.standard_price, linea.cerca_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.cerca_id.id,
									'name':linea.cerca_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.cerca_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.tubo_vertical_id and ml.product_id.default_code=='TUBO_VERTICAL':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.tubo_vertical_id.standard_price, linea.tubo_vertical_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.tubo_vertical_id.id,
									'name':linea.tubo_vertical_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.tubo_vertical_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.tubo_horizontal_id and ml.product_id.default_code=='TUBO_HORIZONTAL':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.tubo_horizontal_id.standard_price, linea.tubo_horizontal_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.tubo_horizontal_id.id,
									'name':linea.tubo_horizontal_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.tubo_horizontal_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.tubo_arriostre_id and ml.product_id.default_code=='TUBO_ARRIOSTRE':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.tubo_arriostre_id.standard_price, linea.tubo_arriostre_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.tubo_arriostre_id.id,
									'name':linea.tubo_arriostre_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.tubo_arriostre_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.mano_obra_id and ml.product_id.default_code=='MANO_OBRA':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.mano_obra_id.standard_price, linea.mano_obra_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.mano_obra_id.id,
									'name':linea.mano_obra_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.mano_obra_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.tuberia_marco_id and ml.product_id.default_code=='TUBERIA_MARCO':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.tuberia_marco_id.standard_price, linea.tuberia_marco_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.tuberia_marco_id.id,
									'name':linea.tuberia_marco_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.tuberia_marco_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.tuberia_diagonal_id and ml.product_id.default_code=='TUBERIA_DIAGONAL':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.tuberia_diagonal_id.standard_price, linea.tuberia_diagonal_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.tuberia_diagonal_id.id,
									'name':linea.tuberia_diagonal_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.tuberia_diagonal_id.uom_id.id,
									'tax_id':imp_id,
									#'price_unit':linea.tubo_arriostre_id.list_price,#revisar como lo hace el odoo en sale_order
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.refuerzo_horizontal_id and ml.product_id.default_code=='REFUERZO_HORIZONTAL':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.refuerzo_horizontal_id.standard_price, linea.refuerzo_horizontal_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.refuerzo_horizontal_id.id,
									'name':linea.refuerzo_horizontal_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.refuerzo_horizontal_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					elif linea.tuberia_columnas_id and ml.product_id.default_code=='TUBERIA_COLUMNAS':
						productos_dict[ml.product_id.default_code]=localdict['result']
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						price_currency=self._get_price_currency( cr, uid, ids, linea.tuberia_columnas_id.standard_price, linea.tuberia_columnas_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.tuberia_columnas_id.id,
									'name':linea.tuberia_columnas_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':linea.tuberia_columnas_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':price_currency,
									'price_unit_cost':price_currency,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
					else:
						productos_dict[ml.product_id.default_code]=localdict['result']
						#######################################################
						vals={}
						#print "print: "+str(ml.product_id.taxes_id[0].id)
						precio_unidad=0
						#if ml.product_id.type!="service":
						precio_unidad=ml.product_id.standard_price
						precio_unidad=self._get_price_currency( cr, uid, ids, precio_unidad, ml.product_id.currency_id, context=None)
						vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':ml.product_id.id,
									'name':ml.product_id.name,
									'product_uom_qty':float(localdict['result']),
									'product_uom':ml.product_id.uom_id.id,
									'tax_id':imp_id,
									'price_unit':precio_unidad,
									'price_unit_cost':precio_unidad,
									})
						self.pool.get('sale.order.line').create(cr, uid, vals, context=context)
				if linea.servicio_total_id:
					print"IF SERVICIO TOTAL"
					vals={}
					vals.update({
									'order_id':ids[0],
									'materials_list_id':linea.materials_list_id.id,
									'product_id':linea.servicio_total_id.id,
									'name':linea.servicio_total_id.name,
									'product_uom_qty':1,
									'product_uom':linea.servicio_total_id.uom_id.id,
									#'tax_id':imp_id,
									'price_unit': 0,
									'price_unit_cost': 0,
									})
					self.pool.get('sale.order.line').create(cr, uid, vals, context=context)

				#CARGAR MONTOS EN SERVICIOS TOTALES
				sale_order_line_obj=self.pool.get('sale.order.line')
				#TODO APARENTA JUNTAR TODAS LAS LISTAS DE MATERIALES EN UN SOLO SERVICIO TOTAL
				conditions = sale_order_line_obj.search(cr, uid, [('order_id','=',ids[0])])
				for sale_line in sale_order_line_obj.browse(cr, uid, conditions,context=context):
					print"FORRRRRRRRRRRRRRRRRRR Prodddddddddddd: "+str(self.get_products(cr, uid, ids, sale_line.materials_list_id.id, context=None))
					print"FORRRRRRRRRRRRRRRRRRR Servvvvvvvvvvvvvvvvv: "+str(self.get_services(cr, uid, ids, sale_line.materials_list_id.id, context=None))
					if sale_line.product_id and sale_line.product_id.servicio_total==True and sale_line.price_unit==0:
						utilidad_x_lista=(self.get_products(cr, uid, ids, sale_line.materials_list_id.id, context=None)*0.7)+(self.get_services(cr, uid, ids, sale_line.materials_list_id.id, context=None)*0.7)
						sale_order_line_obj.write(cr, uid, [sale_line.id], {'price_unit': utilidad_x_lista},context=context)

		return True
	def _get_price_currency(self, cr, uid, ids, amount, product_currency, context=None):
		print"GET_CURRENCYYYYYYYYYYYYYYYY"
		price=0.00
		rate=False
		sale_order_obj=self.browse(cr, uid, ids, context=context)[0]
		date_order=sale_order_obj.date_order
		if product_currency.id!=sale_order_obj.pricelist_id.currency_id.id:
			if product_currency.name=="USD": #PASA DE DOLARES A COLONES
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',product_currency.id),('name','<=',date_order)],order='name desc')
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				if rate.rate!=0:
					price=amount/(rate.rate)
					print"DOLARES A COLONES: "+str(price)
			else: #PASA DE COLONES A DOLARES#TODO
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',sale_order_obj.pricelist_id.currency_id.id),('name','<=',date_order)],order='name desc')
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				price=amount*(rate.rate)
				print"COLONES A DOLARES: "+str(price)
		else:
			price=amount
			print"PRECIO NO CAMBIA: "+str(price)
			print "product_currency: "+str(product_currency.name)
			print "sale_order_currency: "+str(sale_order_obj.pricelist_id.currency_id.name)
		return price
	
	def action_cancel(self, cr, uid, ids, context=None):
		res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
		sale_order_obj=self.pool.get('sale.order').browse(cr, uid, ids[0], context=context)
		#print"PROYECTOOOOOOOOOOOOOOO: "+str(sale_order_obj.proyecto.id)
		if sale_order_obj.proyecto:
			#print "SIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII	"
			self.pool.get('project.project').unlink(cr, uid, [sale_order_obj.proyecto.id], context=None)
		return True
	def action_button_confirm(self, cr, uid, ids, context=None):
		sale_order_obj=self.pool.get('sale.order').browse(cr, uid, ids[0], context=context)
		res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
		if sale_order_obj.genera_proyecto==True:
			vals={}
			vals.update({
						'name': "Proyecto-"+sale_order_obj.name,
						'partner_id': sale_order_obj.partner_id.id,
						'currency_id2': sale_order_obj.pricelist_id.currency_id.id,
						'precio_venta': sale_order_obj.amount_untaxed,
						'costos': False,
						'utilidad': False,
						})
			p=self.pool.get('project.project').create(cr, uid, vals, context=context)
			for l in sale_order_obj.order_line:
				if l.product_id.type=='product':
					self.pool.get('mc.bom.presupuestado').create(cr, uid, {
						'project_id': p,
						'product_id': l.product_id.id,
						'name': l.name,
						'order_id': l.order_id.id,
						'product_uom_qty': l.product_uom_qty,
						'product_uom': l.product_uom.id
					}, context=context)
			self.write(cr, uid, ids, {'proyecto': p},context=context)
		return True
sale_order()

class sale_order_line(osv.osv):
	_inherit = 'sale.order.line'
	def _amount_line_cost(self, cr, uid, ids, field_name, arg, context=None):
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			price = line.price_unit_cost * (1 - (line.discount or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
			cur = line.order_id.pricelist_id.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
		return res
	
	def _amount_price_unit_cost(self, cr, uid, ids, field_name, arg, context=None):
		##montos de los totales de tpa y tps
		order_id_num=self.browse(cr, uid, ids, context=context)[0].order_id.id
		#print "printTTTTTTTTTTTTTTTTTTTTTTTT: "+str(order_id_num)
		lines_obj = self.pool.get('sale.order.line')
		conditions = lines_obj.search(cr, uid, [('order_id', '=', order_id_num)])
		amount_tpa=0
		amount_tps=0
		if context is None:
			context = {}
		for line in lines_obj.browse(cr, uid, conditions, context=context):
			if line.product_id.type!='service':
				amount_tpa=amount_tpa+(line.product_uom_qty*line.product_id.list_price)
			else:
				amount_tps=amount_tps+(line.product_uom_qty*line.product_id.standard_price)
		#############################################
		#print "amount_tpaaaaaaaaaaaaaaaaaaaaaaaaa: "+str(amount_tpa)
		#print "amount_tpsssssssssssssssssssssssss: "+str(amount_tps)
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			if line.product_id:
				if line.product_id.type=="service":
					if amount_tps!=0:
						res[line.id] = (line.product_id.standard_price)*0.5 + (amount_tpa*0.5/amount_tps)
					else:
						res[line.id] = (line.product_id.standard_price)*0.5 + (amount_tpa*0.5)
					#res[line.id] = line.product_id.standard_price
				else:
					res[line.id] = line.price_unit
		return res
	_columns = {
		#'price_unit_cost': fields.function(_amount_price_unit_cost, string='Precio unidad', digits_compute= dp.get_precision('Product Price')),
		'price_unit_cost': fields.float('Precio unidad Cost', digits_compute= dp.get_precision('Product Price')),
		#'price_unit_cost': fields.function(_amount_price_unit_cost, string='Precio unidad', digits_compute= dp.get_precision('Product Price')),
		'price_subtotal_cost': fields.function(_amount_line_cost, string='Subtotal Cost', digits_compute= dp.get_precision('Account')),
		'materials_list_id': fields.many2one('materials.list','Lista de materiales'),
		}

	def _get_price_currency(self, cr, uid, ids, amount, product_currency, pricelist, date_order, context=None):
		print"GET COSTTTTTTTTTTTTT CURRENCY"
		price=0.00
		rate=False
		pricelist_id=self.pool.get('product.pricelist').browse(cr, uid, pricelist, context=context)
		if product_currency.id!=pricelist_id.currency_id.id:
			if product_currency.name=="USD": #PASA DE DOLARES A COLONES
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',product_currency.id),('name','<=',date_order)],order='name desc')
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				if rate.rate!=0:
					price=amount/(rate.rate)
					print"DOLARES A COLONES: "+str(price)
			else: #PASA DE COLONES A DOLARES
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',pricelist_id.currency_id.id),('name','<=',date_order)],order='name desc')
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				price=amount*(rate.rate)
				print"COLONES A DOLARES: "+str(price)
		else:
			price=amount
			print"PRECIO NO CAMBIA: "+str(price)
			print "product_currency: "+str(product_currency.name)
			print "sale_order_currency: "+str(pricelist_id.currency_id.name)
		return price

	def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
			uom=False, qty_uos=0, uos=False, name='', partner_id=False,
			lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):

		res=super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
			uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
			lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
		if product:
			p=self.pool.get('product.product').browse(cr, uid, product, context=context)
			value=res.get('value')
			value.update({'price_unit_cost': self._get_price_currency(cr, uid, ids, p.standard_price, p.currency_id, pricelist, date_order, context=context)})
			res.update({'value': value})
		return res

sale_order_line()
class sale_order_materials_line(osv.osv):
	_name = 'sale.order.materials.line'
	_columns = {
		'order_id': fields.many2one('sale.order','Orden Padre'),
		'materials_list_id': fields.many2one('materials.list','Lista de materiales',required=True),
		'description': fields.text('Descripción'),
		'cerca_id': fields.many2one('product.product','Cerca'),
		#'quantity': fields.float('Cantidad'),
		'cantidad_metros': fields.float('Cantidad de Metros'),
		'altura_cerca': fields.float('Altura de la cerca'),
		'instalado_sobre': fields.selection([('suelo','Suelo'), ('concreto','Concreto')],'Instalado sobre'),
		'tubo_vertical_id': fields.many2one('product.product','Tubo Vertical'),
		'tacos_tubo': fields.boolean('Tacos de Tubo'),
		'separacion_vertical': fields.float('Separación Vertical'),
		'tubo_horizontal': fields.boolean('Tubo Horizontal'),
		'tubo_horizontal_id': fields.many2one('product.product','Tubo Horizontal'),
		'cantidad_lineas': fields.float('Cantidad de Líneas'),
		'arriostre': fields.boolean('Arriostre'),
		'tubo_arriostre_id': fields.many2one('product.product','Tubo Arriostre'),
		'separacion_arriostre': fields.float('Separación Arriostre'),
		'cacheras': fields.boolean('Cacheras'),
		'cantidad_cacheras': fields.float('Cantidad cacheras'),
		'alambre_navaja': fields.float('Cantidad de líneas de alambre navaja'),
		'alambre_pua': fields.float('Cantidad de líneas de alambres de púas'),
		'pintura': fields.boolean('Pintura'),
		'servicio_total_id': fields.many2one('product.product','Servicio Total', help="Agrupa todos el monto de todos los servicios al Cargar las listas de materiales."),
		'mano_obra_id': fields.many2one('product.product', 'Mano de obra'),
		'type': fields.selection([('cerca','Cerca'),('porton','Portón')],'Tipo'),
		####
		'ancho_porton': fields.float('Ancho del portón'),
		'altura_porton': fields.float('Altura deL portón'),
		'tipo_porton': fields.selection([('abatir','De abatir'),('corredizo','Corredizo')],'Tipo de portón'),
		'tuberia_marco_id': fields.many2one('product.product','Tubería del marco'),#domain tubos
		'tuberia_diagonal': fields.boolean('Tubería diagonal'),
		'tuberia_diagonal_id': fields.many2one('product.product','Tubería diagonal'),#domain tubos
		'cantidad_diagonales': fields.float('Cantidad de diagonales'),
		'refuerzo_horizontal': fields.boolean('Tubería refuerzo horizontal'),
		'refuerzo_horizontal_id': fields.many2one('product.product','Tubería refuerzo horizontal'),#domain tubos
		'cantidad_refuerzos_horizontales': fields.float('Cantidad de refuerzos horizontales'),
		'cantidad_hojas': fields.integer('Cantidad de hojas'),
		'tensores': fields.boolean('Tensores'),
		'tuberia_columnas_id': fields.many2one('product.product','Tubería de las columnas'),#domain tubos
		#posiblemente requiera que salgan los monto en esta seccion tambien
		#pero se pensó poner en la vista formulario la gran mayoria de campos
		}
	_defaults = {
			'type': 'cerca',
		}
	def onchange_materiales(self, cr, uid, ids, materials_list_id, context=None):
		if not materials_list_id:
			return True
		materials_line_obj=self.pool.get("materials.list").browse(cr, uid, materials_list_id, context=context)
		return {'value': {'description':materials_line_obj.name}}
sale_order_materials_line()



class project_bitacora(osv.osv):
	_name = 'mc.proyectos.bitacora'
	_columns = {
		'proyecto_id': fields.many2one('project.project', ondelete='cascade', required=True),
		'name': fields.many2one('account.invoice','Factura', required=False),
		'invoice_line_id': fields.many2one('account.invoice.line','Linea de factura', required=False),
		'picking_id': fields.many2one('stock.picking','Orden', required=False),
		'monto': fields.float('Monto'),
		'currency_id': fields.many2one('res.currency','Moneda'),
		'date_invoice':fields.date('Fecha de Factura'),
		}
project_bitacora()

class BomPresupuestado(osv.osv):
	_name = 'mc.bom.presupuestado'
	_columns = {
		'project_id': fields.many2one('project.project', ondelete='cascade', required=True),
		'order_id': fields.many2one('sale.order', 'Pedido de Venta', required=True),
		'name': fields.text('Descripción', required=True),
		'product_id': fields.many2one('product.product', 'Producto'),
		'product_uom_qty': fields.float('Cantidad', digits_compute= dp.get_precision('Product UoS')),
		'product_uom': fields.many2one('product.uom', 'Unidad de medida '),
	}

BomPresupuestado()

class BomEjecutado(osv.osv):
	_name = 'mc.bom.ejecutado'
	_columns = {
		'project_id': fields.many2one('project.project', ondelete='cascade', required=True),
		'picking_id': fields.many2one('stock.picking', 'Orden', required=True),
		'name': fields.text('Descripción', required=True),
		'product_id': fields.many2one('product.product', 'Producto'),
		'product_uom_qty': fields.float('Cantidad', digits_compute= dp.get_precision('Product UoS')),
		'product_uom': fields.many2one('product.uom', 'Unidad de medida '),
	}

BomEjecutado()

class mc_project_project(osv.osv):
	_inherit = 'project.project'
	def _get_utilidad(self, cr, uid, ids, name, args, context=None):
		vals={}
		for i in self.browse(cr, uid, ids, context=context):
			vals[i.id]=float(i.precio_venta)-float(i.costos)
		return vals
	def _get_costo(self, cr, uid, ids, name, args, context=None):
		vals={}
		total_costo=0.00
		bitacora_obj = self.pool.get('mc.proyectos.bitacora')
		conditions = bitacora_obj.search(cr, uid, [('proyecto_id','=',ids[0])])
		for b in bitacora_obj.browse(cr, uid, conditions, context=context):
			if b.date_invoice:
				total_costo+=self._get_price_currency(cr, uid, ids, b.monto, b.currency_id, b.date_invoice)
		for i in self.browse(cr, uid, ids, context=context):
			vals[i.id]=float(total_costo)
		return vals
	_columns = {
		'precio_venta': fields.float('Precio Venta'),
		'costos': fields.function(_get_costo, string='Costos',type='float', store=False),
		'utilidad': fields.function(_get_utilidad, string='Utilidad',type='float', store=False),
		'bitacora': fields.one2many('mc.proyectos.bitacora','proyecto_id','Bitácora'),
		'bom_presupuestado_line': fields.one2many('mc.bom.presupuestado','project_id','Bom Presupuestado'),
		'bom_ejecutado_line': fields.one2many('mc.bom.ejecutado','project_id','Bom Ejecutado'),
		'currency_id2': fields.many2one('res.currency','Moneda', help="Moneda tomada desde el pedido de venta"),
		}

	def _get_price_currency(self, cr, uid, ids, amount, bitacora_currency, date_invoice, context=None):
		price=0.00
		rate=False
		project_obj=self.browse(cr, uid, ids, context=context)[0]
		if bitacora_currency.id!=project_obj.currency_id2.id:
			if bitacora_currency.name=="USD": #PASA DE DOLARES A COLONES
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',bitacora_currency.id),('name','<=',date_invoice)],order='name desc')
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				if rate.rate!=0:
					price=amount/(rate.rate)
					print"DOLARES A COLONES: "+str(price)
			else: #PASA DE COLONES A DOLARES#TODO
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',project_obj.currency_id2.id),('name','<=',date_invoice)],order='name desc')
				print"MONEDAAAAAAAAAAAAAAAAAAAAAAAA: ",project_obj.currency_id2.name
				print"FECHAAAAAAAAAAAAAAAAAAAAAAAAA: ",date_invoice
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				price=amount*(rate.rate)
				print"COLONES A DOLARES: "+str(price)
		else:
			price=amount
			print"PRECIO NO CAMBIA: "+str(price)
			print "project_currency: "+str(bitacora_currency.name)
			print "project_obj_currency: "+str(project_obj.currency_id2.name)
		return price
mc_project_project()

class account_invoice(osv.osv):
	_inherit = 'account.invoice'
	
	def invoice_validate(self, cr, uid, ids, context=None):
		res=super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
		self.write(cr, uid, ids, {'state':'open'}, context=context)
		invoice_line_obj = self.pool.get('account.invoice.line')
		proyecto_obj = self.pool.get('project.project')
		bitacora_obj = self.pool.get('mc.proyectos.bitacora')
		# Busqueda de información para las líneas de factura.
		for invoice in self.browse(cr, uid, ids, context=None):
			if invoice.type == 'in_invoice':
				for ln in invoice.invoice_line:
					for invoice_line in invoice_line_obj.browse(cr, uid, [ln.id], context=None):
						monto_costo=invoice_line.price_subtotal
						if invoice_line.project_id.id:
							# Aumentar el monto de gasto en el proyecto.
							data_project=proyecto_obj.browse(cr, uid, [invoice_line.project_id.id], context=None)[0]
							conditions_bitacora = bitacora_obj.search(cr, uid, [('proyecto_id','=',data_project.id),('name','=',invoice.id)])
							print "CONDITIONSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS: "+str(conditions_bitacora)
							if conditions_bitacora:#ya existe
								#write bitacora
								data_bitacora=bitacora_obj.browse(cr, uid, conditions_bitacora, context=None)[0]
								bitacora_obj.write(cr, uid, data_bitacora.id, {'monto': float(data_bitacora.monto+monto_costo) },context=context)
							else:
								#create bitacora
								bitacora_obj.create(cr, uid, {'name':invoice.id, 'invoice_line_id':invoice_line.id, 'monto': monto_costo,'currency_id': invoice.currency_id.id, 'proyecto_id':data_project.id, 'date_invoice': invoice.date_invoice},context=context)
							#proyecto_obj.write(cr, uid, data_project.id, {'costos': float(data_project.costos+costos)},context=context)
		return res
	def action_cancel(self, cr, uid, ids, context=None):
		res=super(account_invoice, self).action_cancel(cr, uid, ids, context=context)
		bitacora_obj = self.pool.get('mc.proyectos.bitacora')
		invoice_line_obj = self.pool.get('account.invoice.line')
		for ln in self.browse(cr, uid, ids[0], context=None).invoice_line:
			#invoice_line = invoice_line_obj.browse(cr, uid, ids[0], context=None)
			conditions_bitacora = bitacora_obj.search(cr, uid, [('invoice_line_id','=',ln.id)])
			bitacora_obj.unlink(cr, uid, conditions_bitacora, context=context)
			print "CANCELARRRRRRRRRRRRRR: "+str(conditions_bitacora)
		return res
account_invoice()

class account_invoice_line(osv.osv):
	_inherit = 'account.invoice.line'
	_columns = {
		'project_id': fields.many2one('project.project','Proyecto'),
		}
account_invoice_line()

class stock_picking_out(osv.osv):
	_inherit = 'stock.picking.out'
	_columns = {
		'project_id': fields.many2one('project.project','Proyecto'),
		}
	def onchange_project_id(self, cr, uid, ids, project_id, context=None):
		if not ids:
			raise osv.except_osv(('Error'),("\n Los cambios no han sido aplicados: Debería intentar guardar primero el formulario."))
			return True
		move_lines_obj = self.pool.get('stock.move')
		conditions = move_lines_obj.search(cr, uid, [('picking_id', '=', ids[0])])
		move_lines=move_lines_obj.browse(cr, uid, conditions, context=context)
		for m in move_lines:
			m.write({'project_id':project_id})
		return True
stock_picking_out()

class stock_picking(osv.osv):
	_inherit = 'stock.picking'
	_columns = {
		'project_id': fields.many2one('project.project','Proyecto'),
		}
stock_picking()

class stock_move(osv.osv):
	_inherit = 'stock.move'
	_columns = {
		'project_id': fields.many2one('project.project','Proyecto'),
		'dev_origin_move_id': fields.many2one('stock.move','Movimiento origen de devolucion'),
		}
stock_move()

class stock_partial_picking(osv.osv_memory):
	_inherit = 'stock.partial.picking'
	def _get_price_currency(self, cr, uid, ids, amount, product_currency, project, date_invoice, context=None):
		price=0.00
		rate=False
		if product_currency.id!=project.currency_id2.id:
			if product_currency.name=="USD": #PASA DE DOLARES A COLONES
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',product_currency.id),('name','<=',date_invoice)],order='name desc')
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				if rate.rate!=0:
					price=amount/(rate.rate)
					print"DOLARES A COLONES: "+str(price)
			else: #PASA DE COLONES A DOLARES#TODO
				rate_obj=self.pool.get('res.currency.rate')
				conditions = rate_obj.search(cr, uid, [('currency_id','=',project.currency_id2.id),('name','<=',date_invoice)],order='name desc')
				rate=rate_obj.browse(cr, uid, conditions,context=context)[0]
				price=amount*(rate.rate)
				print"COLONES A DOLARES: "+str(price)
		else:
			price=amount
			print"PRECIO NO CAMBIA: "+str(price)
			print "project_currency: "+str(product_currency.name)
			print "project_obj_currency: "+str(project.currency_id2.name)
		return price

	def _partial_move_for(self, cr, uid, move, context=None):
		res = super(stock_partial_picking, self)._partial_move_for(cr, uid, move, context=context)
		res.update({'project_id': move.project_id.id})
		return res
	
	def do_partial(self, cr, uid, ids, context=None):#ESTÁ PONIENDO LINEAS POR SEPARADO #TODO
		res = super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
		partial_line_obj=self.browse(cr, uid, ids[0], context=context).move_ids
		bitacora_obj = self.pool.get('mc.proyectos.bitacora')
		move_line_obj = self.pool.get('account.invoice.line')
		dev=False
		partial_line_obj_sorted = sorted(partial_line_obj, key=lambda partial_line_obj: partial_line_obj.project_id.id)#LISTA DE LINEAS ORDENAS POR PROYECTO

		bitacora_dict=[]
		current_project=0

		#####################################
		first=True
		monto_costo=0.00
		pos=0
		for l in partial_line_obj_sorted:
			if l.project_id:

				if l.wizard_id.picking_id.type=='in':
					project_product_uom_qty=l.quantity*-1
				else:
					project_product_uom_qty=l.quantity

				if l.product_id.type=='product':
					self.pool.get('mc.bom.ejecutado').create(cr, uid, {
						'project_id': l.project_id.id,
						'product_id': l.product_id.id,
						'name': l.product_id.name,
						'picking_id': l.wizard_id.picking_id.id,
						'product_uom_qty': project_product_uom_qty,
						'product_uom': l.product_uom.id
					}, context=context)
				if first:
					current_project=l.project_id
				if current_project.id!=l.project_id.id:
					if l.wizard_id.picking_id.type=='in':
						monto_costo=monto_costo*-1
					bitacora_dict.append({'picking_id': l.wizard_id.picking_id.id ,'monto': monto_costo,'currency_id': current_project.currency_id2.id, 'proyecto_id': current_project.id, 'date_invoice': l.wizard_id.picking_id.date})
					monto_costo=0.00
					current_project=l.project_id
				monto_costo+=self._get_price_currency(cr, uid, ids, (l.product_id.standard_price*l.quantity), l.product_id.currency_id, current_project, l.wizard_id.picking_id.date)

				if pos==len(partial_line_obj_sorted)-1:
					if l.wizard_id.picking_id.type=='in':
						monto_costo=monto_costo*-1
					bitacora_dict.append({'picking_id': l.wizard_id.picking_id.id ,'monto': monto_costo,'currency_id': current_project.currency_id2.id, 'proyecto_id': current_project.id, 'date_invoice': l.wizard_id.picking_id.date})
				first=False
				pos+=1
		#####################################

		#CREATE BITACORA
		for b in bitacora_dict:
			bitacora_obj.create(cr, uid, b,context=context)
		#raise osv.except_osv(('Progra!'),("\n DIS"))
		return res

stock_partial_picking()

class stock_partial_picking_line(osv.TransientModel):
	_inherit = 'stock.partial.picking.line'
	_columns = {
		'project_id': fields.many2one('project.project','Proyecto'),
		}
stock_partial_picking_line()

class stock_return_picking(osv.osv_memory):
	_inherit = 'stock.return.picking'

	def create_returns(self, cr, uid, ids, context=None):
		#res = super(stock_return_picking, self).create_returns(cr, uid, ids, context=context)
		"""
		 Creates return picking.
		 @param self: The object pointer.
		 @param cr: A database cursor
		 @param uid: ID of the user currently logged in
		 @param ids: List of ids selected
		 @param context: A standard dictionary
		 @return: A dictionary which of fields with values.
		"""
		if context is None:
			context = {} 
		record_id = context and context.get('active_id', False) or False
		move_obj = self.pool.get('stock.move')
		pick_obj = self.pool.get('stock.picking')
		uom_obj = self.pool.get('product.uom')
		data_obj = self.pool.get('stock.return.picking.memory')
		act_obj = self.pool.get('ir.actions.act_window')
		model_obj = self.pool.get('ir.model.data')
		wf_service = netsvc.LocalService("workflow")
		pick = pick_obj.browse(cr, uid, record_id, context=context)
		data = self.read(cr, uid, ids[0], context=context)
		date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
		set_invoice_state_to_none = True
		returned_lines = 0
		
#		Create new picking for returned products

		seq_obj_name = 'stock.picking'
		new_type = 'internal'
		if pick.type =='out':
			new_type = 'in'
			seq_obj_name = 'stock.picking.in'
		elif pick.type =='in':
			new_type = 'out'
			seq_obj_name = 'stock.picking.out'
		new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
		new_picking = pick_obj.copy(cr, uid, pick.id, {
										'name': _('%s-%s-return') % (new_pick_name, pick.name),
										'move_lines': [], 
										'state':'draft', 
										'backorder_id': False,
										'type': new_type,
										'date':date_cur, 
										'invoice_state': data['invoice_state'],
		})
		
		val_id = data['product_return_moves']
		for v in val_id:
			data_get = data_obj.browse(cr, uid, v, context=context)
			mov_id = data_get.move_id.id
			if not mov_id:
				raise osv.except_osv(_('Warning !'), _("You have manually created product lines, please delete them to proceed"))
			new_qty = data_get.quantity
			move = move_obj.browse(cr, uid, mov_id, context=context)
			new_location = move.location_dest_id.id
			returned_qty = move.product_qty
			for rec in move.move_history_ids2:
				returned_qty -= rec.product_qty

			if returned_qty != new_qty:
				set_invoice_state_to_none = False
			if new_qty:
				returned_lines += 1
				new_move=move_obj.copy(cr, uid, move.id, {
											'product_qty': new_qty,
											'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
											'picking_id': new_picking, 
											'state': 'draft',
											'location_id': new_location, 
											'location_dest_id': move.location_id.id,
											'date': date_cur,
											'prodlot_id': data_get.prodlot_id.id,
											'dev_origin_move_id': move.id,
				})
				move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]}, context=context)
		if not returned_lines:
			raise osv.except_osv(_('Warning!'), _("Please specify at least one non-zero quantity."))

		if set_invoice_state_to_none:
			pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'}, context=context)
		wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
		pick_obj.force_assign(cr, uid, [new_picking], context)
		# Update view id in context, lp:702939
		model_list = {
				'out': 'stock.picking.out',
				'in': 'stock.picking.in',
				'internal': 'stock.picking',
		}
		#raise osv.except_osv(('Progra!'),("\n create_returns"))
		return {
			'domain': "[('id', 'in', ["+str(new_picking)+"])]",
			'name': _('Returned Picking'),
			'view_type':'form',
			'view_mode':'tree,form',
			'res_model': model_list.get(new_type, 'stock.picking'),
			'type':'ir.actions.act_window',
			'context':context,
		}
stock_return_picking()