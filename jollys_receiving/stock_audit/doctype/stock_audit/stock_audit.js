// Copyright (c) 2024, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Audit', {
    onload: function(frm) {
        // Hides Add Row button from warehouses child table
        frm.get_field('warehouses').grid.cannot_add_rows = true;
        // Hides Delete button from warehouses child table
        frm.set_df_property('warehouses', 'cannot_delete_rows', 1);

        if(frm.doc.location != 'KG Warehouse - JP') {
            frm.fields_dict.warehouses.grid.update_docfield_property('this_priority', "hidden", 1);
            frm.fields_dict.warehouses.grid.update_docfield_property('capacity', "hidden", 1);
            frm.fields_dict.warehouses.grid.update_docfield_property('capacity', "read_only", 1);
            frm.fields_dict.warehouses.grid.update_docfield_property('capacity', "read_only", 1);
        }
    },
    
    refresh: function(frm) {
        if(frm.doc.location == 'KG Warehouse - JP') {
            frm.set_df_property('add_warehouse', 'hidden', 0);
        }

        if(!frm.is_new()) {
            frm.set_df_property('scan_code', 'hidden', 1);
            frm.set_df_property('section_break_hwht', 'hidden', 1);
            frm.set_df_property('item_name', 'hidden', 0);
            frm.set_df_property('item_code', 'read_only', 1);
            frm.set_df_property('section_break_rrxi', 'hidden', 0);
            frm.set_df_property('posting_details_section', 'hidden', 0);
            frm.set_df_property('barcode_details_section', 'hidden', 0);
            frm.set_df_property('expiration_dates_section', 'hidden', 0);
            frm.set_df_property('units_of_measure_section', 'hidden', 0);
            frm.set_df_property('supplier_details_section', 'hidden', 0);
            frm.set_df_property('warehouse_details_section', 'hidden', 0);
        }

        if(frm.doc.docstatus == 1 || frm.doc.docstatus == 2) {
            frm.set_df_property('add_warehouse', 'hidden', 1);
            
            if(frm.doc.set_posting_time == 0) {
                frm.set_df_property('set_posting_time', 'hidden', 1);
            }
        }
    },

    scan_code: function(frm) {
        if(frm.doc.scan_code) {
            frm.save();
        }
    },
    
    set_posting_time: function(frm) {
        if(frm.doc.set_posting_time) {
            frm.set_df_property('posting_date', 'read_only', 0);
            frm.set_df_property('posting_time', 'read_only', 0);
        } else {
            frm.set_df_property('posting_date', 'read_only', 1);
            frm.set_df_property('posting_time', 'read_only', 1);
        }
        frm.refresh_field('posting_date');
        frm.refresh_field('posting_time');
    },
    
    add_warehouse: function(frm) {
        let dialog = new frappe.ui.Dialog({
            title: 'Add Warehouse',
            fields: [
                {
                    label: 'Warehouse',
                    fieldname: 'warehouse',
                    fieldtype: 'Data',
                    reqd: 1 
                },
                {
                    label: 'Capacity',
                    fieldname: 'capacity',
                    fieldtype: 'Float',
                    reqd: 1 
                },
                {
                    label: 'Priority',
                    fieldname: 'priority',
                    fieldtype: 'Int',
                    reqd: 1 
                },
                {
                    label: 'Actual QTY',
                    fieldname: 'actual_qty',
                    fieldtype: 'Int',
                    reqd: 1 
                }
            ],
            size: 'small',
            primary_action_label: 'Add',
            primary_action(values) {
                let existing_warehouse = frm.doc.warehouses.find(warehouse => warehouse.warehouse === values.warehouse);
    
                if (existing_warehouse) {
                    frappe.msgprint('The selected warehouse is already warehouse list.');
                    return;
                }
                let erp_qty = frappe.call({
                    method: 'jollys_receiving.api.get_erp_qty',
                    args: {
                        stock_audit: frm.doc.name,
                        warehouse: values.warehouse
                    }
                });
                
                let warehouse = frm.add_child('warehouses', {
                    item_code: frm.doc.item_code,
                    item_name: frm.doc.item_name,
                    warehouse: values.warehouse,
                    capacity: values.capacity,
                    this_priority: values.priority,
                    actual_qty: values.actual_qty,
                    is_in_warehouse: true,
                    is_new_warehouse: true,
                    erp_qty: erp_qty 
                });
                
                frm.refresh_field('warehouses');
                dialog.hide();
            }
        });

        dialog.fields_dict.warehouse.$input.on('change', function() {
            let warehouse = dialog.fields_dict.warehouse.get_value();

            if (warehouse) {
                frappe.call({
                    method: 'jollys_receiving.api.check_warehouse_exists',
                    args: {
                        warehouse_name: warehouse
                    }
                });
            }
        });
        
        dialog.fields_dict.warehouse.$input.on('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                dialog.fields_dict.capacity.input.focus();
            }
        });

        dialog.show();
    },
}); 

frappe.ui.form.on('Stock Audit Location', {
    is_in_warehouse: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if(!row.is_in_warehouse) {
            frappe.model.set_value(cdt, cdn, 'actual_qty', 0);
            frm.fields_dict['warehouses'].grid.grid_rows_by_docname[cdn].toggle_editable('actual_qty', false);
            frappe.model.set_value(cdt, cdn, 'capacity', 0);
            frm.fields_dict['warehouses'].grid.grid_rows_by_docname[cdn].toggle_editable('capacity', false);
            frappe.model.set_value(cdt, cdn, 'this_priority', 0);
            frm.fields_dict['warehouses'].grid.grid_rows_by_docname[cdn].toggle_editable('this_priority', false);
        } else {
            frm.fields_dict['warehouses'].grid.grid_rows_by_docname[cdn].toggle_editable('actual_qty', true);
            frm.fields_dict['warehouses'].grid.grid_rows_by_docname[cdn].toggle_editable('capacity', true);
            frm.fields_dict['warehouses'].grid.grid_rows_by_docname[cdn].toggle_editable('this_priority', true);
        }
    }
});