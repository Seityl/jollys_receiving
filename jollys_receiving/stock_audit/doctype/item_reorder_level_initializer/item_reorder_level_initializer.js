// Copyright (c) 2025, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Reorder Level Initializer", {
    onload: function(frm) {
        // Hides Add Row button from items child table
        frm.get_field('items').grid.cannot_add_rows = true;
    },

    refresh: function(frm) {
        frm.disable_save();
        frm.add_custom_button(__('Apply Changes'), function() {
            frm.events.apply_changes(frm);
        }).removeClass("btn-default").addClass("btn-primary");
    },

    add_item: function(frm) {
        let dialog = new frappe.ui.Dialog({
            title: 'Add Item',
            fields: [
                {
                    label: 'Item Code',
                    fieldname: 'item_code',
                    fieldtype: 'Link',
                    options: 'Item',
                    reqd: 1 
                },
                {
                    label: 'Re-order Level',
                    fieldname: 'warehouse_reorder_level',
                    fieldtype: 'Float',
                    reqd: 1 
                },
                {
                    label: 'Re-order Qty',
                    fieldname: 'warehouse_reorder_qty',
                    fieldtype: 'Float',
                    reqd: 1 
                },
                {
                    label: 'Store',
                    fieldname: 'store',
                    fieldtype: 'Select',
                    options: 'All Stores\nKG Stock - JP\nMega Retail - JP\nGG Stock - JP\nJPPM Stock - JP\nJPMini Stock - JP',
                    reqd: 1 
                }
            ],
            size: 'small',
            primary_action_label: 'Add',
            primary_action: async function(values) {
                erpnext.utils.remove_empty_first_row(frm, 'items');
                let existing_item = frm.doc.items.find(item => 
                    item.item_code === values.item_code && (
                        item.store === 'All Stores' || 
                        values.store === 'All Stores' || 
                        item.store === values.store
                    )
                );
            
                if (existing_item) {
                    frappe.msgprint('This item/store combination already exists in the table.');
                    dialog.hide();
                    return;
                }
                
                const reorderCheck = await frappe.call({
                    method: 'jollys_receiving.api.check_existing_reorder',
                    args: {
                        item_code: values.item_code,
                        warehouse: values.store
                    },
                    freeze_message: 'Checking Existing Reorder...',
                    freeze: true
                });

                if (reorderCheck.message.exists) {
                    frappe.show_alert(__("Item {0} already has reorder levels in the system. Skipped.", [values.item_code]));
                    dialog.hide();
                    return;
                }

                frappe.call({
                    method: 'jollys_receiving.api.get_item_name',
                    args: {
                        item_code: values.item_code
                    },
                    callback: function(r) {
                        if(r.message) {
                            var d = frappe.model.add_child(cur_frm.doc, 'Item Reorder Level Initializer Item', 'items');
                            d.item_code = values.item_code;
                            d.item_name = r.message;
                            d.warehouse_reorder_level = values.warehouse_reorder_level;
                            d.warehouse_reorder_qty = values.warehouse_reorder_qty;
                            d.store = values.store;
                            refresh_field('items');
                            dialog.hide();
                        } else {
                            console.log(r)
                        }
                    }
                });
            }
        });
        dialog.show();
    },

    add_items_from_pr: function (frm) {
        var d = new frappe.ui.Dialog({
            title: __('Add Items from Purchase Receipt'),
            fields: [
                {
                    fieldname: 'purchase_receipt',
                    fieldtype: 'Link',
                    label: __('Purchase Receipt'),
                    options: 'Purchase Receipt',
                    reqd: 1,
                    get_query: function () {
                        return { 
                            filters: {
                                docstatus: 1
                            }
                        };
                    },
                },
            ],
            primary_action_label: 'Add Items',
            primary_action: async function(values) {
                try {
                    const result = await frappe.call({
                        method: 'jollys_receiving.api.fetch_purchase_receipt_details',
                        freeze: true,
                        freeze_message: 'Fetching Items...',
                        args: {
                            purchase_receipt_name: values['purchase_receipt']
                        }
                    });
                    
                    if (result.message.status === 'success') {
                        erpnext.utils.remove_empty_first_row(frm, 'items');
                        
                        for (const item of result.message.purchase_receipt_items) {
                            const existingInTable = frm.doc.items.find(d => d.item_code === item.item_code);

                            if (existingInTable) {
                                frappe.show_alert(__("Item {0} already exists in the table. Skipped.", [item.item_code]));
                                continue;
                            }
                            
                            const reorderCheck = await frappe.call({
                                method: 'jollys_receiving.api.check_existing_reorder',
                                args: {
                                    item_code: item.item_code
                                },
                                freeze_message: 'Checking Existing Reorder...',
                                freeze: true
                            });

                            if (reorderCheck.message.exists) {
                                frappe.show_alert(__("Item {0} already has reorder levels in the system. Skipped.", [item.item_code]));
                                continue;
                            }

                            const d = frappe.model.add_child(frm.doc, 'Item Reorder Level Initializer Item', 'items');
                            d.item_code = item.item_code;
                            d.item_name = item.item_name;
                            d.warehouse_reorder_level = 0;
                            d.warehouse_reorder_qty = 0;
                            d.store = 'All Stores';
                        }
                        
                        refresh_field('items');
                    } else {
                        frappe.show_alert({ message: result.message.message, indicator: 'red' }, 10);
                    }
                } catch (error) {
                    console.error(error);
                    frappe.show_alert(__("Error processing items"), 5);
                } finally {
                    d.hide();
                }
            }
        });
        d.show();
    },

    add_items_from_po: function (frm) {
        var d = new frappe.ui.Dialog({
            title: __('Add Items from Purchase Order'),
            fields: [
                { 
                    fieldname: 'purchase_order',
                    fieldtype: 'Link',
                    label: __('Purchase Order'),
                    options: 'Purchase Order',
                    reqd: 1,
                },
            ],
            primary_action_label: 'Add Items',
            primary_action: async function(values) {
                try {
                    const result = await frappe.call({
                        method: 'jollys_receiving.api.fetch_purchase_order_details',
                        freeze: true,
                        freeze_message: 'Fetching Items...',
                        args: {
                            purchase_order_name: values['purchase_order']
                        }
                    });

                    if (result.message.status === 'success') {
                        erpnext.utils.remove_empty_first_row(frm, 'items');
                        
                        for (const item of result.message.purchase_order_items) {
                            const existingInTable = frm.doc.items.find(d => d.item_code === item.item_code);

                            if (existingInTable) {
                                frappe.show_alert(__("Item {0} already exists in the table. Skipped.", [item.item_code]));
                                continue;
                            }

                            const reorderCheck = await frappe.call({
                                method: 'jollys_receiving.api.check_existing_reorder',
                                args: {
                                    item_code: item.item_code
                                },
                                freeze_message: 'Checking Existing Reorder...',
                                freeze: true
                            });

                            if (reorderCheck.message.exists) {
                                frappe.show_alert(__("Item {0} already has reorder levels in the system. Skipped.", [item.item_code]));
                                continue;
                            }

                            const d = frappe.model.add_child(frm.doc, 'Item Reorder Level Initializer Item', 'items');
                            d.item_code = item.item_code;
                            d.item_name = item.item_name;
                            d.warehouse_reorder_level = 0;
                            d.warehouse_reorder_qty = 0;
                            d.store = 'All Stores';
                        }
                        
                        refresh_field('items');
                    } else {
                        frappe.show_alert({ message: result.message.message, indicator: 'red' }, 10);
                    }
                } catch (error) {
                    console.error(error);
                    frappe.show_alert(__("Error processing items"), 5);
                } finally {
                    d.hide();
                }
            }
        });
        d.show();
    },

    apply_changes: function(frm) {
        if (!frm.doc.items || frm.doc.items.length === 0) {
            frappe.msgprint(__("No items to process"));
            return;
        }
    
        frappe.confirm(__("Apply reorder levels and clear table?"), async () => {
            try {
                if (frm.is_dirty()) {
                    await frm.save();
                }
    
                const result = await frappe.call({
                    method: 'jollys_receiving.api.apply_reorder_levels',
                    args: {
                        items: frm.doc.items
                    },
                    freeze: true,
                    freeze_message: 'Updating items...'
                });
    
                if (!result.exc) {
                    frm.doc.items = [];
                    refresh_field('items');
                    frm.dirty();
                    await frm.save();
                    frappe.show_alert(__('Applied to {0} items', [result.message.length]));
                }
            } catch (error) {
                frappe.handle_error(error);
            }
        });
    }
});