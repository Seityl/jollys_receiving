# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StockAuditLocation(Document):
	pass

@frappe.whitelist()
def get_item_bins_data(item_code):
	item_bins = []

	try:
		bin_list = frappe.get_all('Bin',
			filters={'item_code':  item_code},
			fields=['name']
		)

		for current_bin in bin_list:
			current_bin_qty = frappe.db.get_value('Bin', current_bin.name, 'actual_qty')
			current_bin_warehouse = frappe.db.get_value('Bin', current_bin.name, 'warehouse')
			current_bin_parent_warehouse = frappe.db.get_value('Warehouse', current_bin_warehouse, 'parent_warehouse')

			if(current_bin_parent_warehouse == 'KG Warehouse - JP'): 
				item_bins.append({
					'warehouse': current_bin_warehouse,
					'erp_qty': current_bin_qty 
				})			

		return item_bins

	except Exception as e:
		frappe.throw(f'Error: {e}')