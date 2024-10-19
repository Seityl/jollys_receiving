# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

kg_warehouses = ['KG Warehouse - JP','KG Stationary - JP','KG Pets - JP','KG Personal Care - JP','KG OTC - JP','KG Oral - JP','KG Household - JP','KG Haircare - JP','KG FOOD_SNACK - JP','KG Flour Room - JP','KG Drinks - JP','KG Cosmetics - JP','KG Chinatown - JP','KG Baby - JP','KG Flour Room - JP']

class StockAudit(Document):
    pass
	# def after_insert(self):
	# 	if not self.item_code:
	# 		return

	# 	self.get_item_name()
	# 	self.get_item_bins()
	# 	self.get_supplier_items()

	# def get_item_name(self):
	# 	item_name = frappe.db.get_value('Item', self.item_code, 'item_name')
	# 	self.item_name = item_name
	# 	self.save()		

	# def get_item_bins(self):
	# 	bin_list = frappe.get_all('Bin',
	# 		filters = {'item_code':  self.item_code},
	# 		fields = ['name']
	# 	)

	# 	for current_bin in bin_list:
	# 		current_bin_qty = frappe.db.get_value('Bin', current_bin.name, 'actual_qty')
	# 		current_bin_warehouse = frappe.db.get_value('Bin', current_bin.name, 'warehouse')
	# 		current_bin_parent_warehouse = frappe.db.get_value('Warehouse', current_bin_warehouse, 'parent_warehouse')

	# 		if(current_bin_parent_warehouse in kg_warehouses): 
	# 			self.append('warehouses', {
	# 				'item_code': self.item_code,
	# 				'item_name': self.item_name,
	# 				'warehouse': current_bin_warehouse,
	# 				'capacity': self.get_warehouse_capacity(current_bin_warehouse),
	# 				'erp_qty': current_bin_qty, 
	# 				'actual_qty': 0 
	# 			})	

	# 	self.save()		

	# def get_warehouse_capacity(self, warehouse):
	# 	putaway_rule = frappe.get_all('Putaway Rule', 
	# 		filters = {'item_code': self.item_code, 'warehouse': warehouse},
	# 		fields = ['name']
	# 	)

	# 	if putaway_rule:	
	# 		return frappe.db.get_value('Putaway Rule', putaway_rule[0].name, 'capacity')

	# 	return 0
	
	# def get_supplier_items(self):
	# 	item_name = frappe.get_all('Item',
	# 		filters = {'item_code': self.item_code},
	# 	)

	# 	item = frappe.get_doc('Item', item_name)
	# 	# supplier_items = item.supplier_items
	
	# 	frappe.msgprint(str(item.name))

