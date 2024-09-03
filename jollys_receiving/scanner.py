import frappe
from frappe import _

def update_uom_conversion_factor(item_code, uom, conversion_rate):
    try:    
        item = frappe.get_doc('Item', item_code)
        
        for i in range(len(item.uoms)):
            if item.uoms[i].uom == uom:
                item.uoms[i].conversion_factor = conversion_rate

        item.save()
        frappe.db.commit()

        return {
            'status': 'success',
            'message': f'{item_code} Conversion Factor changed to: {conversion_rate}'
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

def update_not_verified_scan(receipt_audit_name):
    receipt_audit = frappe.get_doc('Receipt Audit', receipt_audit_name)
    item_table = receipt_audit.items
    barcode = receipt_audit.get('scan_code')
    item_code = get_item_code_from_barcode(barcode)     
    item_name = get_item_name_from_barcode(barcode)   
    
    if item_code:
        try:
            update_item_by_item_code(item_code, item_table, receipt_audit)
            clear_barcode_field(receipt_audit)
            return {
                'status': 'success',
                'message': f'+1 Received QTY:<br><br>{item_code}<br>{item_name}'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'An unexpected error occurred: {str(e)}'
            }

    else:
        clear_barcode_field(receipt_audit)
        return {
            'status': 'error',
            'message': f'Barcode: \'{barcode}\' is invalid'
        }

def update_verified_scan(
        receipt_audit_name, 
        verify_item_code,
        verify_item_name,
        verify_qty=None, 
        verify_scan_uom=None, 
        verify_conversion_rate=None
    ):
    try:
        receipt_audit = frappe.get_doc('Receipt Audit', receipt_audit_name)
        item_table = receipt_audit.items

        update_item_by_item_code(
            verify_item_code,
            item_table,
            receipt_audit,
            verify_scan_qty=verify_qty,
            verify_scan_uom=verify_scan_uom,
            verify_conversion_rate=verify_conversion_rate
        )
        clear_barcode_field(receipt_audit)

        return {
            'status': 'success',
            'message': f'+{verify_qty} Received QTY:<br><br>{verify_item_code}<br>{verify_item_name}'
        }

    except Exception as e:
        clear_barcode_field(receipt_audit)
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

def update_row_conversion_factor_by_item_code(receipt_audit, item_table, item_code):
        for row in item_table:
            row_item_code = row.get('item_code') 

            if row_item_code == item_code:
                row.conversion_rate = 1

                receipt_audit.save()
                frappe.db.commit()
                    

def update_item_by_item_code(
        item_code,
        item_table, 
        receipt_audit, 
        verify_scan_qty=None, 
        verify_scan_uom=None, 
        verify_conversion_rate=None
    ):
    try:
        for row in item_table:
            row_item_code = row.get('item_code') 
            row_qty = row.qty

            if verify_scan_qty and verify_conversion_rate and verify_scan_uom:
                if row_item_code == item_code:
                    if not row_qty:
                        row.qty = verify_scan_qty
                        
                    else:
                        row_qty += verify_scan_qty
                        row.qty = row_qty

                    row.conversion_rate = verify_conversion_rate
                    row.uom = verify_scan_uom

                    receipt_audit.save()
                    frappe.db.commit()
                    
            else:    
                if row_item_code == item_code:
                    if not row_qty:
                        row.qty = 1
                        
                    else:
                        row_qty += 1
                        row.qty = row_qty

                    receipt_audit.save()
                    frappe.db.commit()
        
    except Exception as e:
        frappe.throw(f'Unexpected Error in update_item_by_item_code: {e}')

def get_row_details_from_table(item_table, item_code): 
    row_details = {}

    if item_code and item_table:
        for row in item_table:
            row_item_code = row.get('item_code') 

            if row_item_code == item_code:
                row_details['scan_uom'] = row.uom
                row_details['conversion_rate'] = row.conversion_rate

                return row_details

def get_verify_item_data(receipt_audit_name):
    receipt_audit = frappe.get_doc('Receipt Audit', receipt_audit_name)
    item_table = receipt_audit.items

    try:
        barcode = receipt_audit.get('scan_code')
        item_code = get_item_code_from_barcode(barcode)        
        item_name = get_item_name_from_barcode(barcode)        
        qty = 1 
        scan_uom = get_row_details_from_table(item_table, item_code)['scan_uom']
        conversion_rate = get_row_details_from_table(item_table, item_code)['conversion_rate']

        data = {
            'verify_barcode': barcode,
            'verify_item_code': item_code,
            'verify_item_name': item_name,
            'verify_qty': qty,
            'verify_scan_uom': scan_uom,
            'verify_conversion_rate': conversion_rate
        }

        clear_barcode_field(receipt_audit)

        return data

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

def get_item_code_from_barcode(barcode):
    item = frappe.get_all('Item',
        filters={'barcode': barcode},
        fields=['item_code'],
        as_list=True
    )
    
    if item:
        return item[0][0]

    return None

def get_item_name_from_barcode(barcode):
    try:    
        item = frappe.get_all('Item',
            filters={'barcode': barcode},
            fields=['item_name'],
            as_list=True
        )
        
        if item:
            return item[0][0]

    except Exception as e:
        frappe.msgprint(f'Invalid Barcode. Please try again.{e}')      
        return None

def clear_barcode_field(receipt_audit):
    receipt_audit.scan_code = ''
    receipt_audit.save()
    frappe.db.commit()