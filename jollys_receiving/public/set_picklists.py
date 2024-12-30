import frappe
import erpnext
from erpnext.stock.reorder_item import reorder_item
from frappe.utils import nowdate

# Run script using 'bench execute jollys_receiving.public.set_picklists.set_picklists' in frappe-bench directory

def schedule_set_picklists():
    try:
        frappe.enqueue(
            set_picklists,
            queue="default",
            timeout=86400,
            is_async=True,
            now=False, 
            job_name="Set Pick Lists"
        )

        return {
            'status': True,
            'message': 'success'
        }
        
    except Exception as e:
        return {
            'status': False,
            'message': f'error: {e}'
        }
        
def set_picklists():
    mr_list = reorder_item()

    print('MATERIAL REQUEST | Material Requests To Be Set: {0}'.format(mr_list))

    split_mr_list = []

    for mr in mr_list:
        mr_doc = frappe.get_doc('Material Request', mr.name)

        print('MATERIAL REQUEST | SUCCESS: Loaded MR doc {0}'.format(mr.name))

        try:
            # Should only split material transfers 
            # Deletes non material transfers as well 
            try:
                if  mr_doc.material_request_type != 'Material Transfer':
                    if mr_doc.docstatus == 0:
                        mr_doc.delete() 

                    elif mr_doc.docstatus == 1:
                        mr_doc.docstatus = 2
                        mr_doc.save()
                        mr_doc.delete()

                    print('MATERIAL REQUEST | SUCCESS: Deleted Material Request {0} of type {1}'.format(mr_doc.name, mr_doc.material_request_type))

                    continue
            except: 
                print('MATERIAL REQUEST | ERROR: Something went wrong when deleting Material Request {0} of type {1}'.format(mr_doc.name, mr_doc.material_request_type))

                continue
            
            locations = []
        
            for item in mr_doc.items:
                if item.warehouse not in locations:
                    locations.append(item.warehouse)

                    print('MATERIAL REQUEST | SUCCESS: Added location {0} to locations list'.format(item.warehouse))
        
            print('MATERIAL REQUEST | LOCATIONS LIST: {0}'.format(locations))

            # Should only split material request if it has more than one location
            if len(locations) > 1:
                for location in locations:

                    print('MATERIAL REQUEST | Current Location: {0}'.format(location))

                    # Skip reorders for wholesale and JP Mini
                    if location == 'WS Stock - JP' or location == 'JPMini Stock - JP':

                        print('MATERIAL REQUEST | SUCCESS: Skipped Re-Order for {0}'.format(location))

                        continue
                    
                    new_material_request = frappe.new_doc("Material Request")
                    new_material_request.update({
                        "company": erpnext.get_default_company() or frappe.db.sql("""select name from tabCompany limit 1""")[0][0],
                        "schedule_date": nowdate(),
                        "transaction_date": nowdate(),
                        "material_request_type": mr_doc.material_request_type,
                        'set_warehouse': location
                    })
                    
                    print('MATERIAL REQUEST | {0} | SUCCESS: Updated'.format(location))

                    for item in mr_doc.items:
                        if item.warehouse == location:

                            print('MATERIAL REQUEST | {0} | Item: {1} | Qty: {2}'.format(location, item.item_code, item.qty))
                            
                            new_material_request.append("items", {
                                "item_code": item.item_code,
                                "qty": item.qty,
                                "warehouse": location,
                            })

                    print('MATERIAL REQUEST | {0} | SUCCESS: Finished'.format(location))
                    
                    new_material_request.insert()

                    print('MATERIAL REQUEST | {0} | SUCCESS: Inserted'.format(location))
                    
                    new_material_request.submit()
                    new_material_request.add_comment('Info', f'Auto-Reorders - {nowdate()} - {location}')
                    
                    print('MATERIAL REQUEST | {0} | SUCCESS: Submitted'.format(location))

                    split_mr_list.append(new_material_request.name)

                print('MATERIAL REQUEST | {0} | SUCCESS: Split material request list'.format(mr.name))
                print('Split material request list: {0}'.format(split_mr_list))
                
                if mr_doc.docstatus == 0:
                    mr_doc.delete() 

                elif mr_doc.docstatus == 1:
                    mr_doc.docstatus = 2
                    mr_doc.save()
                    mr_doc.delete()

                print('MATERIAL REQUEST | {0} | SUCCESS: Deleted unsorted material request'.format(mr.name))

                ct = len(split_mr_list)
                cur_ct = 1

                for mr in split_mr_list:
                    create_pick_lists(mr, ct, cur_ct)
                    cur_ct += 1

                print_success_message()

        except Exception as e:
            print('MATERIAL REQUEST | ERROR: {0}'.format(e))
    
@frappe.whitelist()
def create_pick_lists(mr, ct, cur_ct):
    material_request = frappe.get_doc('Material Request', mr)

    print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
    print('PICK LIST | SUCCESS: Got material request {0} for pick list'.format(mr))
    
    new_pick_list = frappe.new_doc('Pick List')

    print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
    print('PICK LIST | SUCCESS: New unsorted pick list')
    
    new_pick_list.update({
        'purpose': material_request.material_request_type,
        'material_request': material_request.name
    })

    print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
    print('PICK LIST | SUCCESS: Updated unsorted pick list')

    for item in material_request.items:
        print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
        print('PICK LIST | Current unsorted Item Code: {0}'.format(frappe.db.get_value('Material Request Item', {'name': item.name}, 'item_code')))
        
        new_pick_list.append('locations', {   
            'item_code': frappe.db.get_value('Material Request Item', {'name': item.name}, 'item_code'),
            'stock_qty': frappe.db.get_value('Material Request Item', {'name': item.name}, 'qty  '),
            'material_request': material_request.name,
            'material_request_item': item.name,
            "conversion_factor": item.conversion_factor,
            "uom": item.uom
        })

    new_pick_list.insert()

    print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
    print('PICK LIST | SUCCESS: Inserted unsorted pick list')

    new_pick_list.parent_warehouse = 'KG Warehouse - JP'
    new_pick_list.save()

    print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
    print('PICK LIST | SUCCESS: Set unsorted parent warehouse to KG')
    
    new_pick_list.set_item_locations()
    new_pick_list.save()
 
    print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
    print('PICK LIST | SUCCESS: Set unsorted item locations')

    groups = {}
    
    for i in new_pick_list.locations:
        key = i.item_group

        if key not in groups:
            groups[key] = [{
                "item_code": i.item_code,
                "qty": i.qty,
                "material_request": i.material_request,
                "material_request_item": i.material_request_item,
                "item_code": i.item_code,
                "item_name": i.item_name,
                "description": i.description,
                "item_group": i.item_group,
                "warehouse": i.warehouse,
                "qty": i.qty,
                "stock_qty": i.stock_qty,
                "picked_qty": i.picked_qty,
                "uom": i.uom,
                "conversion_factor": i.conversion_factor,
                "stock_uom": i.stock_uom,
                "material_request": i.material_request,
                "material_request_item": i.material_request_item
            }]

            print('MATERIAL REQUEST {0}/{1}'.format(cur_ct, ct))
            print('PICK LIST | SUCCESS: Added {0} to item groups'.format(key))

        else:
            groups[key].append({
                "item_code": i.item_code,
                "qty": i.qty,
                "material_request": i.material_request,
                "material_request_item": i.material_request_item,
                "item_code": i.item_code,
                "item_name": i.item_name,
                "description": i.description,
                "item_group": i.item_group,
                "warehouse": i.warehouse,
                "qty": i.qty,
                "stock_qty": i.stock_qty,
                "picked_qty": i.picked_qty,
                "uom": i.uom,
                "conversion_factor": i.conversion_factor,
                "stock_uom": i.stock_uom,
                "material_request": i.material_request,
                "material_request_item": i.material_request_item
            })

    pct = len(groups)
    cur_pct = 1

    for itm in groups:
        split_pick_list = frappe.new_doc('Pick List')

        print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
        print('PICK LIST | SUCCESS: New Sorted List Split')
        
        split_pick_list.update({
            'purpose': new_pick_list.purpose,
            'material_request': new_pick_list.material_request,
            'custom_target_warehouse': new_pick_list.custom_target_warehouse or None,
            'custom_item_group': itm,
        })
        
        print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
        print('PICK LIST | SUCCESS: Pick List Split Updated')

        for j in groups.get(itm):
            print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
            print('PICK LIST | Location: {0} | Group: {1} | Material Request Item: {2}'.format(
                new_pick_list.material_request,
                itm,
                j.get("material_request_item")
                )
            )

            print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
            print('PICK LIST | Material Request Qty: {0}'.format(j.get("qty")))

            split_pick_list.append("locations",{
                "item_code":j.get("item_code"),
                "item_name":j.get("item_name"),
                "description":j.get("description"),
                "item_group":j.get("item_group"),
                "warehouse":j.get("warehouse"),
                "qty":j.get("qty"),
                "stock_qty":j.get("stock_qty"),
                "picked_qty":j.get("picked_qty"),
                "uom":j.get("uom"),
                "conversion_factor":j.get("conversion_factor"),
                "stock_uom":j.get("stock_uom"),
                "material_request":j.get("material_request"),
                "material_request_item":j.get("material_request_item")
            })
            
        split_pick_list.insert()  

        print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
        print('PICK LIST | SUCCESS: Inserted split pick list {0}'.format(split_pick_list.name))

        split_pick_list.parent_warehouse = 'KG Warehouse - JP'
        new_pick_list.save()

        print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
        print('PICK LIST | SUCCESS: Set {0} parent warehouse to KG Warehouse - JP'.format(split_pick_list.name))
        
        try:
            split_pick_list.set_item_locations()
            split_pick_list.save()
            url = f'/app/material-request/{split_pick_list.material_request}'
            link = f'<a href="{url}" target="_blank">{split_pick_list.material_request}</a>'
            split_pick_list.add_comment('Info', f'Item Group: {split_pick_list.custom_item_group} - Split from Material Request: {link}')

            print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
            print('PICK LIST | SUCCESS: Set {0} item locations'.format(split_pick_list.name))

            cur_pct += 1 
            
        except:
            split_pick_list.delete()
            
            print('MATERIAL REQUEST {0}/{1} | PICK LIST {2}/{3}'.format(cur_ct, ct, cur_pct, pct))
            print('PICK LIST | ERROR: Deleted {0}'.format(split_pick_list.name))

    if new_pick_list.docstatus == 0:
        new_pick_list.delete() 

    elif new_pick_list.docstatus == 1:
        new_pick_list.docstatus = 2
        new_pick_list.save()
        new_pick_list.delete()

success_art = """
SSSSS    U   U  CCCCC  CCCCC  EEEEE  SSSSS  SSSSS
S        U   U  C      C      E      S      S    
SSSSS    U   U  C      C      EEEE   SSSSS  SSSSS
    S    U   U  C      C      E          S      S
SSSSS    UUUUU  CCCCC  CCCCC  EEEEE  SSSSS  SSSSS
"""

def print_colored(text, color_code):
    print(f"\033[{color_code}m{text}\033[0m")

def print_success_message():
    print_colored(success_art, "1;32")
    print_colored("\nSUCCESSFULLY COMPLETED\n", "1;36")