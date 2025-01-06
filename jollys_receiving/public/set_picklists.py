import frappe
import erpnext
import datetime
from frappe.utils import nowdate
from erpnext.stock.reorder_item import reorder_item

# Run script using 'bench execute jollys_receiving.public.set_picklists.schedule_set_picklists' in frappe-bench directory

def create_auto_reorder_log(schedule: str, locations: str, message: str):
    log = frappe.new_doc('Auto Reorder Log')
    log.update({
        'date': nowdate(),
        'schedule': schedule,
        'locations': locations,
        'message': message
    })
    log.insert()
    
@frappe.whitelist()
def schedule_set_picklists():
    try:
        reorder_settings = {
            'schedule': {
                'sunday': frappe.db.get_single_value('Auto Reorder Settings', 'sunday'),
                'monday': frappe.db.get_single_value('Auto Reorder Settings', 'monday'),
                'tuesday': frappe.db.get_single_value('Auto Reorder Settings', 'tuesday'),
                'wednesday': frappe.db.get_single_value('Auto Reorder Settings', 'wednesday'),
                'thursday': frappe.db.get_single_value('Auto Reorder Settings', 'thursday'),
                'friday': frappe.db.get_single_value('Auto Reorder Settings', 'friday'),
                'saturday': frappe.db.get_single_value('Auto Reorder Settings', 'saturday')
            },
            'locations': {
                'GG Stock - JP' : frappe.db.get_single_value('Auto Reorder Settings', 'gg'),
                'JPMini Stock - JP' : frappe.db.get_single_value('Auto Reorder Settings', 'mini'),
                'JPPM Stock - JP' : frappe.db.get_single_value('Auto Reorder Settings', 'jppm'),
                'KG Stock - JP' : frappe.db.get_single_value('Auto Reorder Settings', 'kg'),
                'Mega Retail - JP' : frappe.db.get_single_value('Auto Reorder Settings', 'mega'),
                'Mega Stock - JP': frappe.db.get_single_value('Auto Reorder Settings', 'mega_stock'),
                'WS Stock - JP' : frappe.db.get_single_value('Auto Reorder Settings', 'ws')
            }
        }

        frappe.enqueue(
            set_picklists,
            queue='default',
            timeout=86400,
            is_async=True,
            now=False, 
            job_name='Generate & Set Auto Reorders',
            reorder_settings=reorder_settings
        )

        create_auto_reorder_log(schedule='', locations='', message='enqueued the generation of material requests')
        return {
            'status': 'success',
            'message' : 'Enqueued the generation of material requests'
        }
        
    except Exception as e:
        create_auto_reorder_log(schedule='', locations='', message=f'something went wrong when enqueuing the generation of material requests: {e}')
        return {
            'status': 'error',
            'message' : f'something went wrong when enqueuing the generation of material requests: {e}'
        }
    
def set_picklists(reorder_settings: dict):
    schedule = [day for day, value in reorder_settings['schedule'].items() if value == 1]
    locations = [location for location, value in reorder_settings['locations'].items() if value == 1]
    today = datetime.date.today().strftime('%A').lower()
    out = {
        'schedule': ', '.join(schedule),
        'locations': ', '.join(locations),
        'message': ''
    }
    
    if (today not in schedule):
        out['message'] = f'skipped generation of auto reorders on {today}, {nowdate()}'
        create_auto_reorder_log(out['schedule'], out['locations'], out['message'])
        return

    mr_list = reorder_item()
    out['message'] += f'generated material requests: {mr_list}<br>'
    split_mr_list = []

    for mr in mr_list:
        mr_doc = frappe.get_doc('Material Request', mr.name)
        try:
            try:
                if  mr_doc.material_request_type != 'Material Transfer':
                    if mr_doc.docstatus == 0:
                        mr_doc.delete() 

                    elif mr_doc.docstatus == 1:
                        mr_doc.docstatus = 2
                        mr_doc.save()
                        mr_doc.delete()

                    out['message'] += f'deleted material request {mr_doc.name} of type {mr_doc.material_request_type}<br>'
                    continue

            except Exception as e: 
                out['message'] += f'ERROR: Something went wrong when deleting Material Request {mr_doc.name} of type {mr_doc.material_request_type}<br>'
                continue
            
            doc_locations = []
        
            for item in mr_doc.items:
                if item.warehouse not in doc_locations:
                    doc_locations.append(item.warehouse)
        
            for location in doc_locations:
                if location not in locations:
                    out['message'] += f'skipped re-order for {location}<br>'
                    continue
                
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

                new_material_request.insert()
                out['message'] += f'inserted material request for {location}<br>'
                new_material_request.submit()
                new_material_request.add_comment('Info', f'Auto-Reorders - {nowdate()} - {location}')
                out['message'] += f'submitted material request for {location}<br>'
                split_mr_list.append(new_material_request.name)

            out['message'] += f'split material request {mr.name}<br>'
            
            if mr_doc.docstatus == 0:
                mr_doc.delete() 

            elif mr_doc.docstatus == 1:
                mr_doc.docstatus = 2
                mr_doc.save()
                mr_doc.delete()

            out['message'] += f'deleted unsorted material request {mr.name}<br>'
            ct = len(split_mr_list)
            cur_ct = 1

            for mr in split_mr_list:
                create_pick_lists(mr, out, ct, cur_ct)
                cur_ct += 1

            create_auto_reorder_log(out['schedule'], out['locations'], out['message'])

        except Exception as e:
            out['message'] += f'ERROR: something went wrong when splitting material request{e}<br>'
            create_auto_reorder_log(out['schedule'], out['locations'], out['message'])
    
@frappe.whitelist()
def create_pick_lists(mr, out, ct, cur_ct):
    material_request = frappe.get_doc('Material Request', mr)
    item_groups = []

    for item in material_request.items:
        if item.item_group not in item_groups:
            item_groups.append(item.item_group)
            
    pct = len(item_groups)
    cur_pct = 1

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
                        'item_code': frappe.db.get_value('Material Request Item', {'name': item.name}, 'item_code'),
                        'stock_qty': frappe.db.get_value('Material Request Item', {'name': item.name}, 'qty  '),
                        'material_request': material_request.name,
                        'material_request_item': item.name,
                        "conversion_factor": item.conversion_factor,
                        "uom": item.uom
                    })

            def capture_msgprint(message, *args, **kwargs):
                if "is not available in any of the warehouses" in message:
                    out['message'] += f"Insufficient stock for item: {message}<br>"
                elif "is picked in another Pick List" in message:
                    out['message'] += f"Item already picked: {message}<br>"

            frappe.msgprint = capture_msgprint

            sorted_pick_list.insert()
            url = f'/app/material-request/{sorted_pick_list.material_request}'
            link = f'<a href="{url}" target="_blank">{sorted_pick_list.material_request}</a>'
            sorted_pick_list.add_comment('Info', f'Item Group: {sorted_pick_list.custom_item_group} - Split from Material Request: {link}')
            out['message'] += f'material request {material_request.set_warehouse} {cur_ct}/{ct} | inserted sorted pick list {item_group} {cur_pct}/{pct}<br>'
            cur_pct += 1

        except Exception as e:
            sorted_pick_list.delete()
            out['message'] += f'material request {material_request.set_warehouse} {cur_ct}/{ct} | error when inserting sorted pick list {item_group} {cur_pct}/{pct}: {e}<br>'
            out['message'] += f'material request {material_request.set_warehouse} {cur_ct}/{ct} | deleted sorted pick list {item_group} {cur_pct}/{pct}<br>'
            cur_pct += 1
            continue