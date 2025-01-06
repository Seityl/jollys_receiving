import frappe
from frappe import _
from typing import Optional, Union
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, cstr, flt, get_link_to_form
from .scanner import update_row_conversion_factor_by_item_code, update_not_verified_scan, get_verify_item_data, update_verified_scan, update_uom_conversion_factor, get_received_qty_from_row, get_expiration_dates_by_item_code, update_expiration_dates_by_item_code

@frappe.whitelist()
def fetch_purchase_receipt_details(purchase_receipt_name):
    purchase_receipt_doc = frappe.get_doc('Purchase Receipt', purchase_receipt_name)

    if purchase_receipt_doc:
        try:
            return {
                'status': 'success',
                'purchase_receipt_name': purchase_receipt_doc.name,
                'purchase_receipt_supplier': purchase_receipt_doc.supplier,
                'purchase_receipt_supplier_name': purchase_receipt_doc.supplier_name,
                'purchase_receipt_items': purchase_receipt_doc.items
            }
        except:
            return {'status': 'error'}

@frappe.whitelist()
def fetch_purchase_order_details(purchase_order_name):
    purchase_order_doc = frappe.get_doc('Purchase Order', purchase_order_name)

    if purchase_order_doc:
        try:
            return {
                'status': 'success',
                'purchase_order_name': purchase_order_doc.name,
                'purchase_order_supplier': purchase_order_doc.supplier,
                'purchase_order_supplier_name': purchase_order_doc.supplier_name,
                'purchase_order_items': purchase_order_doc.items
            }
        except:
            return {'status': 'error'}

@frappe.whitelist()
def fetch_customs_entry(purchase_receipt_name):
    customs_entries = frappe.db.get_all('Customs Entry', fields=['name'])

    for customs_entry in customs_entries:
        current_doc = frappe.get_doc('Customs Entry', customs_entry)
        consolidation_table = current_doc.consolidation

        if consolidation_table:
            for row in consolidation_table:
                if(row.reference_doctype == 'Purchase Receipt' and row.reference_document == purchase_receipt_name):
                    return {
                        'status':'success',
                        'message': current_doc.name
                    } 

        continue

    return {
        'status':'error',
        'message': 'No associated customs entry found for this purchase receipt'
    } 

@frappe.whitelist()
def fetch_expiration_dates(item_code):
    try:
        return get_expiration_dates_by_item_code(item_code)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def fetch_received_qty_from_row(receiving_name, item_code):
    try:
        return get_received_qty_from_row(receiving_name, item_code)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }
    
@frappe.whitelist()
def fetch_item_data(receiving_name, barcode=None):
    try:
        return get_verify_item_data(receiving_name, barcode)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def update_expiration_dates(item_code, expiration_dates):
    try:
        return update_expiration_dates_by_item_code(item_code, expiration_dates)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def update_not_verified_item(receiving_name):
    try:
        return update_not_verified_scan(receiving_name)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def update_verified_item(
    	receiving_name,
        verify_item_code,
        verify_item_name,
        verify_qty: int = None, 
        verify_conversion_factor: int = None,
        verify_scan_uom: Optional[Union[int, str]] = None
    ):

    try:
        return update_verified_scan(
            receiving_name,
            verify_item_code,
            verify_item_name,
            verify_qty=verify_qty,
            verify_scan_uom=verify_scan_uom,
            verify_conversion_factor=verify_conversion_factor
        )

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def update_item_uom_conversion_factor(item_code, uom, conversion_factor):
    try:
        return update_uom_conversion_factor(item_code, uom, conversion_factor)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def update_row_conversion_factor_by_item_code_code(receiving_name, item_code):
    try:
        receiving = frappe.get_doc('Receiving', receiving_name)
        item_table = receiving.items
        
        update_row_conversion_factor_by_item_code(receiving, item_table, item_code)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def create_stock_entry(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.stock_entry_type = 'Material Transfer'
        target.purpose = 'Material Transfer'
        target.to_warehouse = 'Mega Stock - JP' # Default target warehouse
        target.from_warehouse = 'Port Location - JP' # Default source warehouse
        target.set_missing_values()

    doclist = get_mapped_doc(
		'Receiving',
		source_name,
		{
			'Receiving': {
				'doctype': 'Stock Entry',
                'field_map': {
                    'name': 'custom_reference_receiving'
                }
			},
			'Receiving Item': {
				'doctype': 'Stock Entry Detail',
				'field_map': {
					'warehouse': 's_warehouse',
					'reference_purchase_receipt': 'reference_purchase_receipt',
                    'qty': 'qty',
                    'item_code': 'item_code',
                    'uom':'uom',
                    'conversion_factor':'conversion_factor'
				},
                'condition': lambda item: item.qty > 0
			},
		},
		target_doc,
		set_missing_values,
	)
    
    return doclist

from frappe.utils import nowdate

@frappe.whitelist()
def create_material_request(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.material_request_type = 'Material Transfer'
        target.schedule_date = nowdate()

    doclist = get_mapped_doc(
		'Receiving',
		source_name,
		{
			'Receiving': {
				'doctype': 'Material Request',
                'field_map': {
                    'name': 'custom_reference_receiving'
                }
			},
			'Receiving Item': {
				'doctype': 'Material Request Item',
				'field_map': {
					'warehouse': 's_warehouse',
                    'qty': 'qty',
                    'item_code': 'item_code',
                    'uom':'uom',
                    'conversion_factor':'conversion_factor'
				},
                'condition': lambda item: item.qty > 0
			},
		},
		target_doc,
		set_missing_values,
	)
    
    return doclist
    
@frappe.whitelist()
def create_purchase_order(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.schedule_date = nowdate()

    doclist = get_mapped_doc(
		'Receiving',
		source_name,
		{
			'Receiving': {
				'doctype': 'Purchase Order',
                'field_map': {
                    'name': 'custom_reference_receiving',
                    'supplier': 'supplier'
                }
			},
			'Receiving Item': {
				'doctype': 'Purchase Order Item',
				'field_map': {
					'item_code': 'item_code',
                    'qty': 'qty',
                    'uom':'uom',
                    'conversion_factor':'conversion_factor'
				},
                'condition': lambda item: item.qty > 0
			},
		},
		target_doc,
		set_missing_values,
	)
    
    return doclist

@frappe.whitelist()
def make_receiving_from_purchase_receipt(source_name, target_doc=None):
    doclist = get_mapped_doc(
		'Purchase Receipt',
		source_name,
		{
			'Purchase Receipt': {
				'doctype': 'Receiving',
				 'field_map': {
                    'name': 'reference_purchase_receipt',
                    'supplier': 'supplier',
					'supplier_name': 'supplier_name',
                }
			},
			'Purchase Receipt Item': {
				'doctype': 'Receiving Item',
				'field_map': {
					'warehouse': 's_warehouse',
					'parent': 'reference_purchase_receipt',
					'item_code': 'item_code',
					'item_name': 'item_name',
					'received_qty': 'expected_qty',
					'uom':'uom',
					'conversion_factor':'conversion_factor',
				},
                'field_no_map': {
                    'qty': 0
                }
			},
		},
		target_doc,
	)

    return doclist

@frappe.whitelist()
def make_receiving_from_purchase_order(source_name, target_doc=None):
    doclist = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			'Purchase Order': {
				'doctype': 'Receiving',
				 'field_map': {
                    'name': 'reference_purchase_order',
                    'supplier': 'supplier',
					'supplier_name': 'supplier_name',
                }
			},
			'Purchase Order Item': {
				'doctype': 'Receiving Item',
				'field_map': {
					'parent': 'reference_purchase_order',
					'item_code': 'item_code',
					'item_name': 'item_name',
					'qty': 'expected_qty',
					'uom':'uom',
					'conversion_factor':'conversion_factor'
				},
                'field_no_map': {
                    'qty': 0
                }
			},
		},
		target_doc,
	)

    return doclist

@frappe.whitelist()
def get_erp_qty(stock_audit, warehouse):
    stock_audit = frappe.get_doc('Stock Audit', stock_audit)

    most_recent_bin = frappe.get_all('Bin',
            filters = {'item_code':  stock_audit.item_code, 'warehouse': warehouse},
            fields = ['name'],
            order_by = 'creation'
        )

    if most_recent_bin: 
        current_erp_qty = frappe.db.get_value('Bin', most_recent_bin[0].name, 'actual_qty')
        return current_erp_qty

    return 0

@frappe.whitelist()
def get_item_code_from_barcode(barcode):
    item = frappe.get_all('Item',
        filters={'barcode': barcode},
        fields=['item_code'],
        as_list=True
    )
    
    if item:
        return item[0][0]

    return None

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_item_uoms(doctype, txt, searchfield, start, page_len, filters):
	items = [filters.get("value")]

	return frappe.get_all(
		"UOM Conversion Detail",
		filters={"parent": ("in", items), "uom": ("like", f"{txt}%")},
		fields=["uom"],
		as_list=1,
	)

@frappe.whitelist()
def check_warehouse_exists(warehouse_name):
    try: 
        exists = frappe.db.get_all('Warehouse', filters={'warehouse_name': warehouse_name}, fields=['name'])
        if exists:
            return {
                'status': 'success'
            }
        return {
            'status': 'error', 
            'message': 'Warehouse does not exist'
        }

    except Exception as e:
        return {
            'status': 'error', 
            'message': f'{e}'
        }

@frappe.whitelist()
def get_erp_warehouse(warehouse_name):
    try: 
        return frappe.db.get_all('Warehouse', filters={'warehouse_name': ['like', f'%{warehouse_name}%']}, fields=['name'])[0].name
        
    except Exception as e:
        return {
            'status': 'error', 
            'message': f'{e}'
        }

# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_items_by_barcode(self, barcode):
#     return get_list(
#         'Item',
#         filters={
#             'name': ['in', frappe.get_all(
#                 'Item Barcode',
#                 filters={'barcode': barcode},
#                 fields=['parent']
#             )]
#         },
#         fields=['*']
#     )

# def get_system_managers():
# 	return frappe.db.sql_list(
#         """select parent FROM `tabHas Role`
#         WHERE role='System Manager'
#         AND parent!='Administrator'
#         AND parent IN (SELECT email FROM tabUser WHERE enabled=1)"""
# 	)

# def send_email_notification(mr_list=None):
#     # msg = frappe.render_template('templates/emails/reorder_item.html', {'mr_list': mr_list})
#     frappe.sendmail(recipients=get_system_managers(), subject=_('{[ERPNext] Auto Reorders Generated'), message='msg')