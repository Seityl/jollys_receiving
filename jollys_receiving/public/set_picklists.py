import datetime

import frappe
from frappe.utils import nowdate

import erpnext
from erpnext.stock.reorder_item import reorder_item

# Run script using 'bench execute jollys_receiving.public.set_picklists.schedule_generate_auto_reorder_material_requests' in frappe-bench directory

def get_reorder_settings():
    return frappe.get_single('Auto Reorder Settings')
    
@frappe.whitelist()
def schedule_generate_auto_reorder_material_requests():
    reorder_settings = get_reorder_settings()
    frappe.enqueue(
        generate_auto_reorder_material_requests,
        queue = 'long',
        timeout = 3600,
        is_async = True,
        now = False, 
        job_name = 'Generate Auto Reorder Material Requests',
        reorder_settings = reorder_settings
    )

def schedule_create_pick_lists(split_mr_list):
    frappe.enqueue(
        create_pick_lists,
        queue = 'long',
        timeout = 3600,
        is_async = True,
        now = False,
        job_name = 'Set Auto Reorder Pick Lists',
        split_mr_list = split_mr_list
    )
    
def generate_auto_reorder_material_requests(reorder_settings):
    schedule = [row.day for row in reorder_settings.schedule if row.active == 1]
    locations = [row.location for row in reorder_settings.locations if row.active == 1]
    today = datetime.date.today().strftime('%A')
    if today not in schedule:
        return

    mr_list = reorder_item()
    split_mr_list = []

    for mr in mr_list:
        mr_doc = frappe.get_doc('Material Request', mr.name)

        if  mr_doc.material_request_type != 'Material Transfer':
            if mr_doc.docstatus == 0:
                mr_doc.delete()
                continue

            elif mr_doc.docstatus == 1:
                mr_doc.docstatus = 2
                mr_doc.save()
                mr_doc.delete()
                continue

        doc_locations = []
    
        for item in mr_doc.items:
            if item.warehouse not in doc_locations:
                doc_locations.append(item.warehouse)

        ordered_doc_locations = [loc for loc in locations if loc in doc_locations]

        for location in ordered_doc_locations:
            new_material_request = frappe.new_doc("Material Request")
            new_material_request.update({
                "company": erpnext.get_default_company() or frappe.db.sql("""select name from tabCompany limit 1""")[0][0],
                "schedule_date": nowdate(),
                "transaction_date": nowdate(),
                "material_request_type": mr_doc.material_request_type,
                'set_warehouse': location
            })
            
            for item in mr_doc.items:
                if item.warehouse == location:
                    new_material_request.append("items", {
                        "item_code": item.item_code,
                        "qty": item.qty,
                        "warehouse": location,
                    })

            frappe.db.savepoint('sp2')

            try:
                new_material_request.insert()
                new_material_request.submit()
                new_material_request.add_comment('Info', f'Auto-Reorders - {nowdate()} - {location}')
                frappe.db.commit()

            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(frappe.get_traceback(), "Error in generate_auto_reorder_material_requests()")
                continue

            split_mr_list.append(new_material_request.name)

        frappe.db.savepoint('sp3')
        
        if mr_doc.docstatus == 0 or mr_doc.docstatus == 2:
            try:
                mr_doc.delete()
                frappe.db.commit()

            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(frappe.get_traceback(), "Error in generate_auto_reorder_material_requests()")

        elif mr_doc.docstatus == 1:
            try:
                mr_doc.docstatus = 2
                mr_doc.save()
                mr_doc.delete()
                frappe.db.commit()

            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(frappe.get_traceback(), "Error in generate_auto_reorder_material_requests()")

    schedule_create_pick_lists(split_mr_list)

def create_pick_lists(split_mr_list):
    for mr in split_mr_list:
        material_request = frappe.get_doc('Material Request', mr)
        item_groups = []

        for item in material_request.items:
            if item.item_group not in item_groups:
                item_groups.append(item.item_group)
                
        for item_group in item_groups:
            try:
                sorted_pick_list = frappe.new_doc('Pick List')
                sorted_pick_list.update({
                    'purpose': material_request.material_request_type,
                    'material_request': material_request.name,
                    'parent_warehouse': 'KG Warehouse - JP',
                    'custom_target_warehouse': material_request.set_warehouse,
                    'custom_item_group': item_group
                })

                for item in material_request.items:
                    if item.item_group == item_group:
                        sorted_pick_list.append('locations', {   
                            'item_code': item.item_code,
                            'stock_qty': item.qty,
                            'material_request': material_request.name,
                            'use_serial_batch_fields': 0,
                            'material_request_item': item.name,
                            "conversion_factor": item.conversion_factor,
                            "uom": item.uom
                        })

                frappe.db.savepoint('sp4')

                try:
                    sorted_pick_list.insert()
                    frappe.db.commit()

                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(), "Error in create_pick_lists()")
                    continue
                
                url = f'/app/material-request/{sorted_pick_list.material_request}'
                link = f'<a href="{url}" target="_blank">{sorted_pick_list.material_request}</a>'
                sorted_pick_list.add_comment('Info', f'Item Group: {sorted_pick_list.custom_item_group} - Split from Material Request: {link}')

            except Exception as e:
                frappe.db.savepoint('sp5')

                try:
                    sorted_pick_list.delete()
                    frappe.db.commit()
                    continue

                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(), "Error in set_pick_lists()")
                    continue