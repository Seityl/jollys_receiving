import json
import frappe
from frappe import _

def is_item_code_in_table(item_code, item_table):
    for row in item_table:
        row_item_code = row.get('item_code') 

        if row_item_code == item_code:
            return True

    return False
    
def update_expiration_dates_by_item_code(item_code, expiration_dates):
    item = frappe.get_doc('Item', item_code)

    try:    
        expiration_dates = json.loads(expiration_dates)
        item.custom_expiration_dates_table.clear()

        for expiration_date in expiration_dates:
            item.append('custom_expiration_dates_table', {
                'expiration_date': expiration_date.get('expiration_date'),
            })

        item.save()
        link = f'<a href="/app/item/{item_code}" target="_blank">{item_code}</a>'
        
        return{
            'status': 'success',
            'message': f'Updated expiration dates of {link}'
        } 

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Something went wrong: {e}'
        }
        
def update_uom_conversion_factor(item_code, uom, conversion_factor):
    try:    
        item = frappe.get_doc('Item', item_code)
        
        for i in range(len(item.uoms)):
            if item.uoms[i].uom == uom:
                item.uoms[i].conversion_factor = conversion_factor

                item.save()
                frappe.db.commit()

                return {
                    'status': 'success',
                    'message': f'{item_code} Conversion Factor changed to: {conversion_factor}'
                }

        return {
            'status': 'error',
            'message': f'Error: Could not update Conversion Factor<br><br>UOM "{uom}" does not exist under item: {item_code}'
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

def update_not_verified_scan(receiving_name):
    receiving = frappe.get_doc('Receiving', receiving_name)
    item_table = receiving.items
    barcode = receiving.get('scan_code')
    item_code = get_item_code_from_barcode(barcode)     
    item_name = get_item_name_from_barcode(barcode)   
    
    if item_code:
        if is_item_code_in_table(item_code, item_table):
            try:
                return {
                    'data': update_item_by_item_code(item_code, item_table, receiving),
                    'status': 'success',
                    'message': f'+1 Received QTY:<br><br>{item_code}<br>{item_name}'
                }

            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'An unexpected error occurred: {str(e)}'
                }

        else:
            return {
                'status': 'error',
                'message': 'Scanned Item Not on Receiving'
            }

    else:
        clear_barcode_field(receiving)
        return {
            'status': 'error',
            'message': f'Barcode: \'{barcode}\' is invalid'
        }

def update_verified_scan(
        receiving_name,
        verify_item_code,
        verify_item_name,
        verify_qty=None, 
        verify_scan_uom=None, 
        verify_conversion_factor=None
    ):

    try:
        receiving = frappe.get_doc('Receiving', receiving_name)
        item_table = receiving.items

        response = {'data':
            update_item_by_item_code(
                verify_item_code,
                item_table,
                receiving,
                verify_scan_qty=verify_qty,
                verify_scan_uom=verify_scan_uom,
                verify_conversion_factor=verify_conversion_factor
            ),
            'status': 'success'
        }
        
        if verify_qty > 0:
            response['message'] = f'+{verify_qty} Received QTY<br><br>{verify_item_name}'

        return response

    except Exception as e:
        clear_barcode_field(receiving)

        return {
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }

def update_row_conversion_factor_by_item_code(receiving, item_table, item_code):
    for row in item_table:
        row_item_code = row.get('item_code') 

        if row_item_code == item_code:
            row.conversion_factor = 1

            receiving.save()
            frappe.db.commit()
                
def update_item_by_item_code(
        item_code,
        item_table, 
        receiving, 
        verify_scan_qty=None, 
        verify_scan_uom=None, 
        verify_conversion_factor=None
    ):
    try:
        for row in item_table:
            row_item_code = row.get('item_code') 
            row_qty = row.qty

            if verify_conversion_factor and verify_scan_uom:
                if row_item_code == item_code:
                    if verify_scan_qty:
                        if not row_qty:
                            row.qty = verify_scan_qty
                            
                        else:
                            row_qty += verify_scan_qty
                            row.qty = row_qty

                    row.conversion_factor = verify_conversion_factor
                    row.uom = verify_scan_uom

                    receiving.save()
                    frappe.db.commit()

                    return True
                    
            else:    
                if row_item_code == item_code:
                    if not row_qty:
                        row.qty = 1
                        
                    else:
                        row_qty += 1
                        row.qty = row_qty

                    receiving.save()
                    frappe.db.commit()

                    return True

        return False
        
    except Exception as e:
        frappe.throw(f'Unexpected Error in update_item_by_item_code: {e}')

def get_row_details_from_table(item_table, item_code): 
    row_details = {}

    if item_code and item_table:
        for row in item_table:
            row_item_code = row.get('item_code') 

            if row_item_code == item_code:
                row_details['expected_qty'] = row.expected_qty
                row_details['scan_uom'] = row.uom
                row_details['conversion_factor'] = row.conversion_factor
                row_details['received_qty'] = row.qty

                return row_details

def get_received_qty_from_row(receiving_name, item_code):
    receiving = frappe.get_doc('Receiving', receiving_name)
    item_table = receiving.items
    try:
        received_qty = get_row_details_from_table(item_table, item_code)['received_qty']
        data = {
            'status': 'success',
            'received_qty': received_qty 
        }
        
        return data

    except Exception as e:
            frappe.throw(f'Unexpected Error in update_item_by_item_code: {e}')

def get_verify_item_data(receiving_name, barcode=None):
    receiving = frappe.get_doc('Receiving', receiving_name)
    item_table = receiving.items

    if not barcode:
        barcode = receiving.get('scan_code')

    try:
        item_code = get_item_code_from_barcode(barcode)

        if item_code:        
            item_name = get_item_name_from_barcode(barcode)        
            link = f'<a href="/app/item/{item_code}" target="_blank">{item_code}</a>'
            expected_qty = get_row_details_from_table(item_table, item_code)['expected_qty']
            qty = None 
            scan_uom = get_row_details_from_table(item_table, item_code)['scan_uom']
            conversion_factor = get_row_details_from_table(item_table, item_code)['conversion_factor']
            received_qty = get_row_details_from_table(item_table, item_code)['received_qty']

            data = {
                'status': 'success',
                'verify_barcode': barcode,
                'verify_item_code': item_code,
                'verify_item_name': f'{link}: {item_name}',
                'verify_expected_qty': expected_qty,
                'verify_received_qty': received_qty,
                'verify_qty': qty,
                'verify_scan_uom': scan_uom,
                'verify_conversion_factor': conversion_factor
            }

            clear_barcode_field(receiving)

            return data

        else: 
            clear_barcode_field(receiving)

            return {
                'status': 'error',
                'message': f'Barcode: \'{barcode}\' is invalid'
            }

    except Exception as e:
        return {
            'status': 'error',
            'message': 'Scanned Item Not on Receiving'
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

def get_expiration_dates_by_item_code(item_code):
    try:    
        expiration_dates = frappe.get_doc('Item', item_code).custom_expiration_dates_table
        
        if expiration_dates:
            return{
                'status': 'success',
                'expiration_dates': expiration_dates
            }

        return {
            'status': 'success',
            'expiration_dates': []
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Something went wrong: {e}'
        }

def clear_barcode_field(receiving):
    receiving.scan_code = ''
    receiving.save()
    frappe.db.commit()