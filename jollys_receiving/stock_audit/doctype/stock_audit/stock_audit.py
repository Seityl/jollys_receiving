# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.nestedset import get_descendants_of
from erpnext.controllers.stock_controller import StockController

class StockAudit(StockController):
    def after_insert(self):
        self.get_item_data()

    def validate(self):
        self.validate_posting_time()

        if self.location == 'KG Warehouse - JP':
            self.validate_warehouse_priority()
            self.validate_warehouse_capacity()
        
    def before_submit(self):
        self.validate_qty()
        
    def on_submit(self):
        self.update_item_doc()
        self.update_stock_levels()
        
        if self.location == 'KG Warehouse - JP':
            self.set_putaway_rules()

    def on_update_after_submit(self):
        if self.location == 'KG Warehouse - JP':
            self.disable_inactive_putaway_rules()

    def on_cancel(self):
        self.revert_changes()
        
    def validate_warehouse_capacity(self):
        if not self.warehouses:
            return
            
        for warehouse in self.warehouses:
            if warehouse.is_in_warehouse and warehouse.capacity < warehouse.actual_qty:
                frappe.throw(
                    title = 'Insufficient Capacity Error',
                    msg = _(f'Warehouse Capacity {warehouse.capacity} must be greater than the actual stock level of {warehouse.actual_qty} for warehouse {warehouse.warehouse}.')
                )

    def validate_warehouse_priority(self):
        if not self.warehouses:
            return
        
        priority_set = set()

        for warehouse in self.warehouses:
            if not warehouse.reference_putaway_rule:
                continue

            priority = warehouse.this_priority

            if warehouse.is_stored_here:
                if priority is None:
                    frappe.throw(
                        title='Priority Required',
                        msg=_(f'Warehouse {warehouse.warehouse} must have a priority set.')
                    )

                elif priority < 1:
                    frappe.throw(
                        title='Invalid Priority',
                        msg=_(f'Priority for {warehouse.warehouse} cannot be less than 1.')
                    )

            if priority is not None and priority in priority_set:
                frappe.throw(
                    title='Duplicate Priority',
                    msg=_(f'Priority {warehouse.this_priority} is used multiple times.')
                )

            priority_set.add(priority)

    def validate_qty(self):
        if not self.warehouses:
            return

        for warehouse in self.warehouses:
            most_recent_bin = frappe.get_all('Bin',
                filters = {'item_code':  self.item_code, 'warehouse': warehouse.warehouse},
                fields = ['name'],
                order_by = 'creation desc'
            )

            if most_recent_bin: 
                current_erp_qty = frappe.db.get_value('Bin', most_recent_bin[0].name, 'actual_qty')

                if warehouse.erp_qty != current_erp_qty:
                    warehouse.erp_qty = current_erp_qty
                    
            if warehouse.is_stored_here:
                if warehouse.is_in_warehouse and warehouse.actual_qty == 0:
                    frappe.throw(
                        title = 'Error',
                        msg = _(f'Item is in warehouse {warehouse.warehouse} and Actual Qty is 0.')
                    )

    def set_item_code(self):
        item_code = frappe.get_all('Item',
            filters = {'barcode': self.scan_code},
            fields = ['item_code'],
            as_list = True
        )
        
        if not item_code:
            frappe.throw(
                title = 'Invalid Barcode Error',
                msg = _(f'No item found for barcode {self.scan_code}')
            )

        self.item_code = item_code[0][0]
        self.save()

    def get_child_warehouses(self, parent_warehouse:str) -> list:
        return get_descendants_of("Warehouse", parent_warehouse)

    def get_actual_qty(self, item_code, warehouse):
        actual_qty = frappe.db.get_value(
            'Bin',
            {'item_code': item_code, 'warehouse': warehouse},
            'actual_qty'
        )
        return actual_qty or 0

    def get_item_data(self):
        if not self.item_code and not self.scan_code:
            frappe.throw(
                title = 'Error',
                msg = _(f'No item code or barcode is attached.')
            )

        if not self.item_code and self.scan_code:
            self.set_item_code()
            
        self.get_item_name()
        self.get_item_group()
        self.get_item_description()
        self.get_item_bins()
        self.get_expiration_dates()
        self.get_barcodes()
        self.get_supplier_items()
        self.get_uoms()
        self.save()		

    def get_item_name(self):
        self.item_name = frappe.db.get_value('Item', self.item_code, 'item_name')		
        self.original_item_name = frappe.db.get_value('Item', self.item_code, 'item_name')		

    def get_item_group(self):
        self.item_group = frappe.db.get_value('Item', self.item_code, 'item_group')		
        self.original_item_group = frappe.db.get_value('Item', self.item_code, 'item_group')		

    def get_item_description(self):
        self.item_description = frappe.db.get_value('Item', self.item_code, 'description')		
        self.original_item_description = frappe.db.get_value('Item', self.item_code, 'description')		

    def get_item_bins(self):
        bin_list = frappe.get_all('Bin',
            filters={'item_code': self.item_code},
            fields=['warehouse', 'actual_qty']
        )

        child_warehouses = []
        if self.location == 'KG Warehouse - JP':
            child_warehouses = self.get_child_warehouses(self.location)

        location_processed = False

        for current_bin in bin_list:
            warehouse = current_bin.warehouse
            actual_qty = current_bin.actual_qty

            if actual_qty <= 0:
                if self.location != 'KG Warehouse - JP':
                    continue
                else:
                    reference_rule = self.get_reference_putaway_rule(warehouse)
                    if not reference_rule.get('name'):
                        continue
                    else:
                        self.append('warehouses', {
                            'item_code': self.item_code,
                            'item_name': self.item_name,
                            'warehouse': warehouse,
                            'capacity': self.get_warehouse_capacity(warehouse),
                            'erp_qty': actual_qty,
                            'this_priority': reference_rule.get('priority') or 0,
                            'actual_qty': 0,
                            'is_in_warehouse': 0,
                            'is_stored_here': 1,
                            'reference_putaway_rule': reference_rule.get('name')
                        })
            else:
                if self.location == 'KG Warehouse - JP' and warehouse in child_warehouses:
                    reference_rule = self.get_reference_putaway_rule(warehouse)
                    self.append('warehouses', {
                        'item_code': self.item_code,
                        'item_name': self.item_name,
                        'warehouse': warehouse,
                        'capacity': self.get_warehouse_capacity(warehouse),
                        'erp_qty': actual_qty,
                        'this_priority': reference_rule.get('priority') or 0,
                        'actual_qty': 0,
                        'is_in_warehouse': 1,
                        'is_stored_here': 1,
                        'reference_putaway_rule': reference_rule.get('name')
                    })

                elif warehouse == self.location:
                    self.append('warehouses', {
                        'item_code': self.item_code,
                        'item_name': self.item_name,
                        'warehouse': warehouse,
                        'capacity': self.get_warehouse_capacity(warehouse),
                        'erp_qty': actual_qty,
                        'actual_qty': 0,
                        'is_in_warehouse': 1,
                        'is_stored_here': 1
                    })
                    location_processed = True
                    break
                
        if self.location != 'KG Warehouse - JP' and not location_processed:
            self.append('warehouses', {
                'item_code': self.item_code,
                'item_name': self.item_name,
                'warehouse': self.location,
                'capacity': self.get_warehouse_capacity(self.location),
                'erp_qty': self.get_actual_qty(self.item_code, self.location),
                'actual_qty': 0,
                'is_in_warehouse': 1,
                'is_stored_here': 1
            })

    def get_reference_putaway_rule(self, warehouse):
        putaway_rule = frappe.get_all('Putaway Rule', 
            filters = {'item_code': self.item_code, 'warehouse': warehouse, 'disable': 0},
            fields = ['name']
        )

        if not putaway_rule:
            return {
                'name': None,
                'priority': None
            }
            
        if putaway_rule:	
            putaway_rule_doc = frappe.get_doc('Putaway Rule', putaway_rule[0].name)

            if putaway_rule_doc:
                return {
                    'name': putaway_rule_doc.name,
                    'priority': putaway_rule_doc.priority
                }
    
    def get_warehouse_capacity(self, warehouse):
        putaway_rule = frappe.get_all('Putaway Rule', 
            filters = {'item_code': self.item_code, 'warehouse': warehouse},
            fields = ['name']
        )

        if putaway_rule:	
            capacity = frappe.db.get_value('Putaway Rule', putaway_rule[0].name, 'capacity')
            return float(capacity) if capacity is not None else 0.0

        return 0.0

    def get_supplier_items(self):
        supplier_items = frappe.get_doc('Item', self.item_code).supplier_items

        for supplier_item in supplier_items:
            current_supplier = supplier_item.supplier
            current_supplier_part_no = supplier_item.supplier_part_no

            self.append('supplier_items', {
                'supplier': current_supplier,
                'supplier_part_no': current_supplier_part_no,
            })	

            self.append('original_supplier_items', {
                'supplier': current_supplier,
                'supplier_part_no': current_supplier_part_no,
            })	
        
    def get_barcodes(self):
        barcodes = frappe.get_doc('Item', self.item_code).barcodes

        for current_barcode in barcodes:
            barcode = current_barcode.barcode
            barcode_type = current_barcode.barcode_type
            uom = current_barcode.uom

            self.append('barcodes', {
                'barcode': barcode,
                'barcode_type': barcode_type,
                'uom': uom
            })	

            self.append('original_barcodes', {
                'barcode': barcode,
                'barcode_type': barcode_type,
                'uom': uom
            })	
        
    def get_expiration_dates(self):
        expiration_dates = frappe.get_doc('Item', self.item_code).custom_expiration_dates_table

        for current_expiration_date in expiration_dates:
            expiration_date = current_expiration_date.expiration_date

            self.append('expiration_dates', {
                'expiration_date': expiration_date,
            })	

            self.append('original_expiration_dates', {
                'expiration_date': expiration_date,
            })

    def get_uoms(self):
        uoms = frappe.get_doc('Item', self.item_code).uoms

        for current_uom in uoms:
            uom = current_uom.uom
            conversion_factor = current_uom.conversion_factor

            self.append('uoms', {
                'uom': uom,
                'conversion_factor': conversion_factor,
            })

            self.append('original_uoms', {
                'uom': uom,
                'conversion_factor': conversion_factor,
            })

    def update_supplier_items(self, item_doc, self_supplier_items):
        existing_suppliers = {(item.supplier, item.supplier_part_no) for item in item_doc.supplier_items}
        new_suppliers = {(item.supplier, item.supplier_part_no) for item in self_supplier_items}

        if existing_suppliers != new_suppliers:
            item_doc.supplier_items.clear()

            for supplier_item in self_supplier_items:
                item_doc.append('supplier_items', {
                    'supplier': supplier_item.supplier,
                    'supplier_part_no': supplier_item.supplier_part_no,
                })
                
            return True
            
        return False

    def update_barcodes(self, item_doc, self_barcodes):
        existing_barcodes = {(item.barcode, item.barcode_type, item.uom) for item in item_doc.barcodes}
        new_barcodes = {(barcode.barcode, barcode.barcode_type, barcode.uom) for barcode in self_barcodes}

        if existing_barcodes != new_barcodes:
            item_doc.barcodes.clear()
            
            for barcode in self_barcodes:
                item_doc.append('barcodes', {
                    'barcode': barcode.barcode,
                    'barcode_type': barcode.barcode_type,
                    'uom': barcode.uom
                })
                
            return True
            
        return False

    def update_uoms(self, item_doc, self_uoms):
        existing_uoms = {(item.uom, item.conversion_factor) for item in item_doc.uoms}
        new_uoms = {(uom.uom, uom.conversion_factor) for uom in self_uoms}

        if existing_uoms != new_uoms:
            item_doc.uoms.clear()
            
            for uom in self_uoms:
                item_doc.append('uoms', {
                    'uom': uom.uom,
                    'conversion_factor': uom.conversion_factor,
                })

            return True
            
        return False
    
    def update_expiration_dates(self, item_doc, self_expiration_dates):
        existing_expiration_dates = [expiration_date for expiration_date in item_doc.custom_expiration_dates_table]
        new_expiration_dates = [expiration_date for expiration_date in self_expiration_dates]

        if existing_expiration_dates != new_expiration_dates:
            item_doc.custom_expiration_dates_table.clear()

            for expiration_date in self_expiration_dates:
                item_doc.append('custom_expiration_dates_table', {
                    'expiration_date': expiration_date.expiration_date
                })

            return True
        
        return False

    def update_item_doc(self):
        item_doc = frappe.get_doc('Item', self.item_code)
        updated = False

        if (item_doc.item_name != self.item_name):
            item_doc.item_name = self.item_name
            updated = True

        if (item_doc.item_group != self.item_group):
            item_doc.item_group = self.item_group
            updated = True

        if (item_doc.description != self.item_description):
            item_doc.description = self.item_description
            updated = True

        # Only update child tables if change has been made

        updated |= self.update_supplier_items(item_doc, self.supplier_items)
        updated |= self.update_barcodes(item_doc, self.barcodes)
        updated |= self.update_uoms(item_doc, self.uoms)
        updated |= self.update_expiration_dates(item_doc, self.expiration_dates)

        if updated:
            item_doc.save()
            self.add_linked_comment(item_doc)

    def add_linked_comment(self, doc, new_doc=False, reverted=False):
        url = f'/app/stock-audit/{self.name}'
        link = f'<a href="{url}" target="_blank">{self.name}</a>'

        if new_doc:
            doc.add_comment('Info', f'Created Via Stock Audit {link}')

        elif reverted:
            doc.add_comment('Info', f'Changed Reverted From Stock Audit {link}')

        else:
            doc.add_comment('Info', f'Details Updated Via Stock Audit {link}')

    def update_stock_levels(self):
        for warehouse in self.warehouses:
            # Skip warehouse if newly created for item. Stock will be updated after putaway rule is created.
            if warehouse.is_new_warehouse:
                continue

            # Transfer ERP qty to audit waerhouse if item not in warehouse
            if not warehouse.is_in_warehouse:
                self.create_material_transfer(warehouse, warehouse.warehouse, warehouse.erp_qty, is_excess=True)
                continue
                
            # Skip warehouse if count is accurate
            if warehouse.erp_qty == warehouse.actual_qty:
                continue

            # Transfer difference out of location if ERP QTY more than Actual QTY
            elif warehouse.erp_qty > warehouse.actual_qty:
                difference_qty = warehouse.erp_qty - warehouse.actual_qty
                self.create_material_transfer(warehouse, warehouse.warehouse, difference_qty, is_excess=True)

            # Create material receipt to add difference if Actual QTY more than ERP QTY
            elif warehouse.erp_qty < warehouse.actual_qty:
                difference_qty = warehouse.actual_qty - warehouse.erp_qty
                if not warehouse.reference_putaway_rule:
                    self.create_material_receipt(warehouse, warehouse.warehouse, difference_qty)

                elif warehouse.reference_putaway_rule:
                    putaway_rule_doc = frappe.get_doc('Putaway Rule', warehouse.reference_putaway_rule)
                    self.update_putaway_rule(putaway_rule_doc, warehouse)
                    self.create_material_receipt(warehouse, warehouse.warehouse, difference_qty)

    def update_putaway_rule(self, putaway_rule_doc, warehouse, updated=False):
        if not warehouse.is_stored_here:
            if(putaway_rule_doc.disable == 0):
                putaway_rule_doc.disable = 1
                putaway_rule_doc.priority = warehouse.this_priority
                putaway_rule_doc.capacity = warehouse.capacity
                putaway_rule_doc.save()
                self.add_linked_comment(putaway_rule_doc)
                warehouse.reference_putaway_rule = putaway_rule_doc.name
                self.save()

            return
         
        if(putaway_rule_doc.disable == 1):
                putaway_rule_doc.disable = 0
                updated = True 

        if(putaway_rule_doc.capacity != warehouse.capacity):
                putaway_rule_doc.capacity = warehouse.capacity
                updated = True

        if(putaway_rule_doc.priority != warehouse.this_priority):
                putaway_rule_doc.priority = warehouse.this_priority
                updated = True

        if updated:
            putaway_rule_doc.save()
            warehouse.reference_putaway_rule = putaway_rule_doc.name
            self.save()
            self.add_linked_comment(putaway_rule_doc)

    def create_material_transfer(self, row, from_warehouse, qty:int, to_warehouse=None, is_excess=False):
        if is_excess:
            to_warehouse = 'Stock Audit Warehouse - JP'

        new_material_transfer_doc = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Transfer',
            'company': 'Jollys Pharmacy Limited',
            'from_warehouse': from_warehouse,
            'to_warehouse': to_warehouse,  
            'posting_date': self.posting_date,
            'posting_time': self.posting_time,
            'items': [
                {
                    'item_code': self.item_code,
                    'qty': qty,
                    'uom': 'EACH'
                }
            ]
        })

        new_material_transfer_doc.insert()
        new_material_transfer_doc.set_posting_time = 1
        new_material_transfer_doc.posting_time = self.posting_time
        new_material_transfer_doc.posting_date = self.posting_date
        new_material_transfer_doc.submit()

        row.reference_stock_entry = new_material_transfer_doc.name
        self.save()
        self.add_linked_comment(new_material_transfer_doc, new_doc=True)

    def create_material_receipt(self, row, warehouse, qty:int):
        new_material_receipt_doc = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Receipt',
            'company': 'Jollys Pharmacy Limited',
            'to_warehouse': warehouse,  
            'items': [
                {   
                    'item_code': self.item_code,
                    'qty': qty,
                    'uom': 'EACH'
                }
            ]
        })

        new_material_receipt_doc.insert()
        new_material_receipt_doc.set_posting_time = 1
        new_material_receipt_doc.posting_time = self.posting_time
        new_material_receipt_doc.posting_date = self.posting_date
        new_material_receipt_doc.submit()

        row.reference_stock_entry = new_material_receipt_doc.name
        self.save()
        self.add_linked_comment(new_material_receipt_doc, new_doc=True)

    def create_putaway_rule(self, row, warehouse, capacity:float, priority:int):
        new_putaway_rule_doc = frappe.get_doc({
            'doctype': 'Putaway Rule',
            'item_code': self.item_code,
            'warehouse': warehouse,  
            'capacity': capacity,
            'stock_capacity': capacity,
            'priority': priority,
            'uom': frappe.db.get_value("Item", self.item_code, "stock_uom")
        })
        new_putaway_rule_doc.ignore_validate = True
        new_putaway_rule_doc.insert()
        row.reference_putaway_rule = new_putaway_rule_doc.name
        self.save()
        self.add_linked_comment(new_putaway_rule_doc, new_doc=True)

    def set_putaway_rules(self):
        for warehouse in self.warehouses:
            if not warehouse.is_in_warehouse and not warehouse.is_stored_here:
                putaway_rule = frappe.get_all('Putaway Rule', 
                    filters = {'item_code': self.item_code, 'warehouse': warehouse.warehouse},
                    fields = ['name']
                )
                    
                if putaway_rule:	
                    putaway_rule_doc = frappe.get_doc('Putaway Rule', putaway_rule[0].name)
                    if putaway_rule_doc:
                        putaway_rule_doc.disable = 1
                        putaway_rule_doc.save()

                continue
            
            if warehouse.reference_putaway_rule:
                putaway_rule_doc = frappe.get_doc('Putaway Rule', warehouse.reference_putaway_rule)
                
                if(putaway_rule_doc.warehouse != warehouse.warehouse):	
                    frappe.throw(
                        title='Putaway Rule Error',
                        msg = _(f'Warehouse for Putaway rule {warehouse.reference_putaway_rule} updated after the creation of this Stock Audit.')
                    )

                self.update_putaway_rule(putaway_rule_doc, warehouse)

            else: 
                putaway_rule = frappe.get_all('Putaway Rule', 
                    filters = {'item_code': self.item_code, 'warehouse': warehouse.warehouse},
                    fields = ['name']
                )
                    
                if putaway_rule:	
                    putaway_rule_doc = frappe.get_doc('Putaway Rule', putaway_rule[0].name)
                    if putaway_rule_doc:
                        self.update_putaway_rule(putaway_rule_doc, warehouse)

                else:
                    self.create_putaway_rule(warehouse, warehouse.warehouse, warehouse.capacity, warehouse.this_priority)

                #  Not sure why this works but it does. Do. Not. Modify.
                if warehouse.is_new_warehouse:
                    self.create_material_receipt(warehouse, warehouse.warehouse, warehouse.actual_qty)
        
    def disable_inactive_putaway_rules(self):
        active_putaway_rules = set()
    
        for warehouse in self.warehouses:
            if warehouse.reference_putaway_rule:
                active_putaway_rules.add(warehouse.reference_putaway_rule)
        
        item_putaway_rules = frappe.get_all('Putaway Rule', 
            filters={'item_code': self.item_code},
            fields=['name'],
            as_list=True
        )

        for rule in item_putaway_rules:
            rule_name = rule[0]
            
            if rule_name not in active_putaway_rules:
                doc = frappe.get_doc('Putaway Rule', rule_name)
                
                if not doc.disable:
                    doc.disable = 1
                    doc.save()
                    self.add_linked_comment(doc)
    
    def revert_changes(self):
        item_doc = frappe.get_doc('Item', self.item_code)
        updated = False

        if (item_doc.item_name != self.original_item_name):
            item_doc.item_name = self.original_item_name
            updated = True

        if (item_doc.item_group != self.original_item_group):
            item_doc.item_group = self.original_item_group
            updated = True

        if (item_doc.description != self.original_item_description):
            item_doc.description = self.original_item_description
            updated = True

        # Only update child tables if change has been made

        updated |= self.update_supplier_items(item_doc, self.original_supplier_items)
        updated |= self.update_barcodes(item_doc, self.original_barcodes)
        updated |= self.update_uoms(item_doc, self.original_uoms)
        updated |= self.update_expiration_dates(item_doc, self.original_expiration_dates)

        if updated:
            item_doc.save()
            self.add_linked_comment(item_doc, reverted=True)

        linked_stock_entries = set()
        linked_putaway_rules = set()
    
        for warehouse in self.warehouses:
            if warehouse.reference_stock_entry:
                linked_stock_entries.add(warehouse.reference_stock_entry)

            if warehouse.reference_putaway_rule:
                linked_putaway_rules.add(warehouse.reference_putaway_rule)

        for stock_entry in linked_stock_entries:
            doc = frappe.get_doc('Stock Entry', stock_entry)
            
            if doc.docstatus == 0:
                continue

            elif doc.docstatus == 1:
                doc.docstatus = 2
                doc.save()
                self.add_linked_comment(doc, reverted=True)

        for putaway_rule in linked_putaway_rules:
            doc = frappe.get_doc('Putaway Rule', putaway_rule)

            if doc.disable == 0:
                doc.disable = 1
                doc.save()
                self.add_linked_comment(doc, reverted=True)

            else:
                continue