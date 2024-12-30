# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.utils import get_stock_balance

class QuickReorders(Document):
    pass

@frappe.whitelist()
def get_stock_and_item_details(warehouse, item_code=None, barcode=None):
    out = {}

    if barcode:
        out['item_code'] = frappe.db.get_value('Item Barcode', filters={'barcode': barcode}, fieldname=['parent'])
        
        if not out['item_code']:
            return False

    else:
        out['item_code'] = item_code

    barcodes = frappe.db.get_values('Item Barcode', filters={'parent': out['item_code']}, fieldname=['barcode'])
    out['barcodes'] = [x[0] for x in barcodes]     
    out['qty'] = get_stock_balance(out['item_code'], warehouse)
    out['item_name'] = frappe.db.get_value('Item', filters={'name': out['item_code']}, fieldname=['item_name'])    
    out['description'] = frappe.db.get_value('Item', filters={'name': out['item_code']}, fieldname=['description'])    
    out['warehouse_reorder_level'] = frappe.db.get_value('Item Reorder', filters={'parent': out['item_code'], 'warehouse': warehouse}, fieldname=['warehouse_reorder_level'])    
    out['warehouse_reorder_qty'] = frappe.db.get_value('Item Reorder', filters={'parent': out['item_code'], 'warehouse': warehouse}, fieldname=['warehouse_reorder_qty'])    

    return out

@frappe.whitelist()
def update_item_reorder(item_code, warehouse, warehouse_reorder_level, warehouse_reorder_qty):
    item_doc = frappe.get_doc('Item', item_code)

    try:
        for current_reorder in item_doc.reorder_levels:
            if current_reorder.warehouse == warehouse:
                current_reorder.warehouse_group = frappe.db.get_value('Warehouse', filters={'name': warehouse}, fieldname=['parent_warehouse'])
                current_reorder.warehouse_reorder_level = warehouse_reorder_level
                current_reorder.warehouse_reorder_qty = warehouse_reorder_qty
                current_reorder.material_request_type = 'Transfer'
                item_doc.save()
                item_doc.add_comment('Info', f'Reorder For {warehouse} Updated Using Quick Reorders')
                
                return True
        
        item_doc.append('reorder_levels', {
            'warehouse_group': frappe.db.get_value('Warehouse', filters={'name': warehouse}, fieldname=['parent_warehouse']),
            'warehouse': warehouse,
            'warehouse_reorder_level': warehouse_reorder_level,
            'warehouse_reorder_qty': warehouse_reorder_qty,
            'material_request_type': 'Transfer'
        })
        
        item_doc.save()
        item_doc.add_comment('Info', f'Reorder For {warehouse} Added Using Quick Reorders')

        return True

    except Exception as e:
        frappe.throw(f'Unexpected error has occured: {e}')

# # def create_quick_log(item_code, warehouse, o_warehouse_reorder_qty, o_warehouse_reorder_level, warehouse_reorder_qty, warehouse_reorder_level):
# @frappe.whitelist()
# def create_quick_log():
#     quick_log = frappe.get_doc({
#         'doctype': 'Quick Reorders Log',
#         # 'user': frappe.session.user,
#         'warehouse': 'GG Stock - JP',
#         # 'item': item_code,
#         # 'o_warehouse_reorder_qty': o_warehouse_reorder_qty,
#         # 'o_warehouse_reorder_level': o_warehouse_reorder_level,
#         # 'n_warehouse_reorder_qty': warehouse_reorder_qty,
#         # 'n_warehouse_reorder_level': warehouse_reorder_level,
#     })
    
#     quick_log.insert()

#     # return 'created'
#     # frappe.db.commit()