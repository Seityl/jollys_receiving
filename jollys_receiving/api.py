import frappe
from frappe import _
from typing import Optional, Union
from frappe.model.mapper import get_mapped_doc
from .scanner import update_row_conversion_factor_by_item_code, update_not_verified_scan, get_verify_item_data, update_verified_scan, update_uom_conversion_factor

@frappe.whitelist()
def update_not_verified_item(receipt_audit_name):
    try:
        return update_not_verified_scan(receipt_audit_name)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def fetch_item_data(receipt_audit_name):
    try:
        return get_verify_item_data(receipt_audit_name)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def update_verified_item(
    	receipt_audit_name,
        verify_barcode, 
        verify_item_code,
        verify_item_name,
        verify_qty: int = None, 
        verify_conversion_factor: int = None,
        verify_scan_uom: Optional[Union[int, str]] = None
    ):

    try:
        return update_verified_scan(
            receipt_audit_name,
            verify_barcode,
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
def update_row_conversion_factor_by_item_code_code(receipt_audit_name, item_code):
    try:
        receipt_audit = frappe.get_doc('Receipt Audit', receipt_audit_name)
        item_table = receipt_audit.items
        
        update_row_conversion_factor_by_item_code(receipt_audit, item_table, item_code)

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

@frappe.whitelist()
def create_stock_entry(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.stock_entry_type = "Material Transfer"
        target.purpose = "Material Transfer"
        target.to_warehouse = 'Mega Stock - JP'
        target.from_warehouse = 'Port Location - JP'
        # target.purchase_receipt_no = 'MAT-PRE-2024-00008'
        target.save()
        target.set_missing_values()

    doclist = get_mapped_doc(
		'Receipt Audit',
		source_name,
		{
			'Receipt Audit': {
				'doctype': 'Stock Entry',
			},
			'Receipt Audit Item': {
				'doctype': 'Stock Entry Detail',
				"field_map": {
					"warehouse": "s_warehouse",
					"reference_purchase_receipt": "reference_purchase_receipt",
                    "qty": "qty",
                    "item_code": "item_code",
                    "uom":"uom",
                    "conversion_factor":"conversion_factor"
				},
			},
		},
		target_doc,
		set_missing_values,
	)
    
    return doclist
    
# Check if the document is being saved for the first time
# def on_update(doc, method):
#     if doc.__islocal:  
#         doc.is_first_save = True
#         doc.save()

@frappe.whitelist()
def make_receipt_audit(source_name, target_doc=None):
	doclist = get_mapped_doc(
		"Purchase Receipt",
		source_name,
		{
			"Purchase Receipt": {
				"doctype": "Receipt Audit",
				 'field_map': {
                    'name': 'reference_purchase_receipt',
                }
			},
			"Purchase Receipt Item": {
				"doctype": "Receipt Audit Item",
				"field_map": {
					"warehouse": "s_warehouse",
					"parent": "reference_purchase_receipt",
					"item_code": "item_code",
					"item_name": "item_name",
					"received_qty": "expected_qty",
					"rejected_qty": "qty",
					"uom":"uom",
					"conversion_factor":"conversion_factor"
				},
			},
		},
		target_doc,
	)

	return doclist