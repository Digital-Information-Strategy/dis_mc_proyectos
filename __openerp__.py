# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
        "name" : "Proyectos Malla Ciclon",
        "version" : "1.0",
        "author" : "DIS S.A.",
        "website" : "http://dis.co.cr",
        "category" : "Proyectos",
        "description": """
         Modulo para gestion de proyectos, implementando tambien el manejo de lista de materiales en productos.
         Para el correcto funcionamiento del módulo, es necesario crear los siguientes productos:
        * CERCA
        * TUBO_VERTICAL
        * TUBO_HORIZONTAL
        * TUBO_ARRIOSTRE
        """,
        "depends" : ['base','base_setup','product','sale','project'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "data" : ['dis_mc_proyectos_view.xml', 'security/mc_proyectos_security.xml','security/ir.model.access.csv'],
        "installable": True
}
