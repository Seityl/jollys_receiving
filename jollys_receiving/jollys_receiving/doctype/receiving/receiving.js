// Copyright (c) 2024, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Receiving', {
    onload: function(frm) {
        // Hides Add Row button from items child table
        frm.get_field('items').grid.cannot_add_rows = true;
        // Hides Delete button from items child table
        frm.set_df_property('items', 'cannot_delete_rows', 1);
        
        if(frm.is_new() && frm.doc.reference_purchase_receipt) {
            frappe.call({
                method: 'jollys_receiving.api.fetch_customs_entry',
                freeze: true,
                freeze_message: 'Fetching Customs Entry...',
                args: {
                    purchase_receipt_name: frm.doc.reference_purchase_receipt
                },
                callback: (r) => {
                    if(r.message['status'] == 'success') {
                        frm.set_value('customs_entry', r.message['message']);
                    } else {
                        frappe.show_alert({
                            message: r.message['message'],
                            indicator:'red'
                        }, 10);
                    }
                }
            });
        }
        
        if(frm.doc.scan_code) {
            frm.set_value('scan_code','');
        }

        if(frm.doc.reference_purchase_order) {
            frm.fields_dict['customs_entry'].df.hidden = true;
        }
        
        if(frm.doc.docstatus == 1 || frm.doc.docstatus == 2) {
            // Hide verify scan checkbox when document is submitted
            frm.fields_dict['verify_scan'].df.hidden = true;
            // Hide scan box when document is submitted
            frm.fields_dict['scan_code'].df.hidden = true;
        }
        
        frm.events.show_help(frm);
    },
    
    refresh: function(frm) {
        frm.events.make_custom_buttons(frm);
        frm.events.toggle_more_info_tab(frm);
    },
    
    toggle_more_info_tab: function(frm) {
        if (frm.is_new()) {
            frm.$wrapper.find("[data-fieldname='more_info_tab']").hide();
        } else {
            frm.$wrapper.find("[data-fieldname='more_info_tab']").show();
        }
    },
    
    make_custom_buttons: function (frm) {
        if(frm.is_new()) {
			frm.add_custom_button(
                __("Purchase Order"),
				() => frm.events.get_items_from_purchase_order(frm),
				__("Get Items From")
			); 

			frm.add_custom_button(
                __("Purchase Receipt"),
				() => frm.events.get_items_from_purchase_receipt(frm),
				__("Get Items From")
			);
		}

        if(!frm.is_new() || frm.doc.docstatus == 1) {
            frm.add_custom_button(
                __('Stock Entry'),
                frm.cscript['Stock Entry'],
                __('Create')
            );

            frm.add_custom_button(
                __('Material Request'),
                frm.cscript['Material Request'],
                __('Create')
            );
            
            if(frm.doc.reference_purchase_order) {
                frm.add_custom_button(
                    __('Purchase Order'),
                    frm.cscript['Purchase Order'],
                    __('Create')
                );
            }
        };
	},
    
    show_help: function (frm) {
        if(frm.is_new() & frm.doc.items.length === 0) {
            frappe.show_alert({
                message: 'To create a receiving, please select a Purchase Receipt or Purchase Order to get items from.',
                indicator:'blue'
            }, 60);  
        }
    },

    get_items_from_purchase_receipt: function (frm) {
        var d = new frappe.ui.Dialog({
            title: __('Get Items from Purchase Receipt'),
            fields: [
                {
                    fieldname: 'purchase_receipt',
                    fieldtype: 'Link',
                    label: __('Purchase Receipt'),
                    options: 'Purchase Receipt',
                    reqd: 1,
                    get_query: function () {
                        return { filters: { docstatus: 1} };
                    },
                },
            ],
            primary_action_label: 'Get Items',
            primary_action(values) {
                frappe.call({
                    method: 'jollys_receiving.api.fetch_purchase_receipt_details',
                    freeze: true,
                    freeze_message: 'Fetching Items...',
                    args: {
                        purchase_receipt_name: values['purchase_receipt']
                    },
                    callback: function (r) {
                        frappe.model.clear_table(frm.doc, 'items');
                        frm.events.clear_details(frm);                        
                        
                        if (r.message['status'] === 'success') {
                            frm.set_value('reference_purchase_receipt', values['purchase_receipt'])
                            frm.set_value('supplier_name', r.message['purchase_receipt_supplier_name'])
                            frm.set_value('supplier', r.message['purchase_receipt_supplier'])
                            
                            erpnext.utils.remove_empty_first_row(frm, 'items');
                            
                            $.each(r.message['purchase_receipt_items'], function (i, item) {
                                var d = frappe.model.add_child(cur_frm.doc, 'Receiving Item', 'items');
                                
                                d.s_warehouse = item.warehouse;
                                d.reference_purchase_receipt = values.purchase_receipt;
                                d.item_code = item.item_code;
                                d.item_name = item.item_name;
                                d.expected_qty = item.received_qty;
                                d.uom = item.uom;
                                d.conversion_factor = item.conversion_factor;
                                d.qty = 0;
                            });
                            
                            refresh_field('items');
                            
                        } else if (r.message['status'] === 'error') {
                            frappe.show_alert({
                                message: r.message['message'],
                                indicator:'red'
                            }, 10);
                        }
                        
                        d.hide();
                    },
                });
            },
        });
        
        d.show();
    },

    get_items_from_purchase_order: function (frm) {
        var d = new frappe.ui.Dialog({
            title: __('Get Items from Purchase Order'),
            fields: [
                { 
                    fieldname: 'purchase_order',
                    fieldtype: 'Link',
                    label: __('Purchase Order'),
                    options: 'Purchase Order',
                    reqd: 1,
                    get_query: function () {
                        return { filters: { docstatus: 0} };
                    },
                },
            ],
            primary_action_label: 'Get Items',
            primary_action(values) {
                frappe.call({
                    method: 'jollys_receiving.api.fetch_purchase_order_details',
                    freeze: true,
                    freeze_message: 'Fetching Items...',
                    args: {
                        purchase_order_name: values['purchase_order']
                    },
                    callback: function (r) {
                        frappe.model.clear_table(frm.doc, 'items');
                        frm.events.clear_details(frm);

                        if (r.message['status'] === 'success') {
                            frm.set_value('reference_purchase_order', values['purchase_order']);
                            frm.set_value('supplier_name', r.message['purchase_order_supplier_name']);
                            frm.set_value('supplier', r.message['purchase_order_supplier']);
                            
                            erpnext.utils.remove_empty_first_row(frm, 'items');
                            
                            $.each(r.message['purchase_order_items'], function (i, item) {
                                var d = frappe.model.add_child(cur_frm.doc, 'Receiving Item', 'items');
                                
                                d.s_warehouse = item.warehouse;
                                d.reference_purchase_order = values.purchase_order;
                                d.item_code = item.item_code;
                                d.item_name = item.item_name;
                                d.expected_qty = item.qty;
                                d.uom = item.uom;
                                d.conversion_factor = item.conversion_factor;
                                d.qty = 0;
                            });
                            
                            refresh_field('items');
                            
                        } else if (r.message['status'] === 'error') {
                            frappe.show_alert({
                                message: r.message['message'],
                                indicator:'red'
                            }, 10);
                        }
                        
                        d.hide();
                    },
                });
            },
        });

        d.show();
    },
    
    clear_details: function(frm) {
        frm.set_value('reference_purchase_receipt', '')
        frm.set_value('reference_purchase_order', '')
        frm.set_value('customs_entry', '')
        frm.set_value('supplier_name', '')
        frm.set_value('supplier', '')
    },

    scan_code: function(frm) {
        if (!frm.is_new()) {
            scan_barcode(frm);   
        } else {
            frm.set_value('scan_code', '');            
        }
    },
    
    verify_scan: function(frm) {
        if (!frm.is_new()) {
            if(frm.is_dirty()) {
                frm.save().then(() => {
                    frm.reload_doc();
                });
            }
        } else {
            frm.set_value('verify_scan', 0);   
        }
    }
});

// Data of verify scan dialog
let data = {};

function scan_barcode(frm) {
    if(frm.is_dirty()) {
        frm.save().then(() => {
            if(frm.doc.scan_code) {
                if(frm.doc.verify_scan) {
                    update_verified_item(frm);
                } else {
                    update_not_verified_item(frm);
                }
            }
        });
    }
}

function update_not_verified_item(frm) {
    frappe.call({
        method: 'jollys_receiving.api.update_not_verified_item',
        args: {
            receiving_name: frm.doc.name
        },
        callback: (r) => {
            if(r.message['data']) {
                if(r.message['status'] === 'success') {
                    frappe.show_alert({
                        message: r.message['message'],
                        indicator:'green'
                    }, 10);
                } else {
                    frappe.show_alert({
                        message: r.message['message'],
                        indicator:'red'
                    }, 10);
                }
            } else if(!r.message['data']) {
                frappe.show_alert({
                    message: r.message['message'],
                    indicator:'red'
                }, 10);
            }
        }
    });
}

function update_verified_item(frm) {
    // Fetch item data from table and create scan details dialog
    frappe.call({
        method: 'jollys_receiving.api.fetch_item_data',
        args: {
            receiving_name: frm.doc.name,
        },
        callback: (r) => {
            if(r.message['status'] === 'success') {
                data = {
                    'verify_barcode': r.message['verify_barcode'],
                    'verify_item_code': r.message['verify_item_code'],
                    'verify_item_name': r.message['verify_item_name'],
                    'verify_expected_qty': r.message['verify_expected_qty'],
                    'verify_received_qty': r.message['verify_received_qty'],
                    'verify_qty': r.message['verify_qty'],
                    'verify_scan_uom': r.message['verify_scan_uom'],
                    'verify_conversion_factor': r.message['verify_conversion_factor']
                };        
                dialog = create_verify_dialogue(data, frm);
            } else {
                frappe.show_alert({
                    message: r.message['message'],
                    indicator:'red'
                }, 10);
                frm.reload_doc();
            }
        }
    });
}

async function check_condition(frm, values) {
    return new Promise((resolve) => {
        frappe.call({
            method: 'jollys_receiving.api.fetch_received_qty_from_row',
            args: {
                receiving_name: frm.doc.name,
                item_code: values['verify_item_code']
            },
            callback: (r) => {
                if(r.message['status'] === 'success') {
                    let current_received_qty = r.message['received_qty']; 
                    let will_be_received_qty = values['verify_qty'] + current_received_qty;
                    let expected_qty = values['verify_expected_qty'];

                    if(values['verify_qty']) {
                        if(will_be_received_qty > expected_qty) {
                            resolve(true);
                        } else if(will_be_received_qty = expected_qty) {
                            resolve(false);
                        } else if(will_be_received_qty < expected_qty) {
                            resolve(false);
                        }
                    } else {
                        resolve(false);
                    }
                }
            }
        });
    })
}

function update_row(frm, values, data) {
    frappe.call({
        method: 'jollys_receiving.api.update_verified_item',
        args: {
            receiving_name: frm.doc.name,
            verify_item_code: values['verify_item_code'],
            verify_item_name: values['verify_item_name'],
            verify_qty: values['verify_qty'] || 0,
            verify_scan_uom: values['verify_scan_uom'],
            verify_conversion_factor: values['verify_conversion_factor']
        },
        callback: (r) => {
            if(r.message['status'] === 'success') {
                if(r.message['message'] != null) {
                    frappe.show_alert({
                        message: r.message['message'],
                        indicator:'green'
                    }, 10);
                }

                if(values['verify_conversion_factor'] != data['verify_conversion_factor']) {
                    frappe.call({
                        method: 'jollys_receiving.api.update_item_uom_conversion_factor',
                        args: {
                            receiving_name: frm.doc.name,
                            item_code: values['verify_item_code'],
                            uom: values['verify_scan_uom'],
                            conversion_factor: values['verify_conversion_factor']
                        },
                        callback: (r) => {
                            if(r.message['status'] === 'success') {
                                frappe.show_alert({
                                    message: r.message['message'],
                                    indicator:'green'
                                }, 10);
                            } else {
                                frappe.show_alert({
                                    message: r.message['message'],
                                    indicator:'red'
                                }, 10);
                                frappe.call({
                                    method: 'jollys_receiving.api.update_row_conversion_factor_by_item_code_code',
                                    args: {
                                        receiving_name: frm.doc.name,
                                        item_code: values['verify_item_code'],
                                    },
                                    callback: function() {
                                        frm.reload_doc();
                                    }
                                });
                            }
                        }
                    }); 
                } 
                frm.reload_doc();
            } else {
                frappe.show_alert({
                    message: r.message['message'],
                    indicator:'red'
                }, 10);
                frm.reload_doc();
            }
        }
    });
}

function create_verify_dialogue(data, frm) {
    let d = new frappe.ui.Dialog({
        title: '<b>Scan Details</b>',
        fields: 
        [{
            label: 'Item Code',
            fieldname: 'verify_item_code',
            fieldtype: 'Data',
            read_only: 1, 
            hidden: 1
        },
        {
            label: 'Item',
            fieldname: 'verify_item_name',
            fieldtype: 'Text',
            read_only: 1, 
        },
        {
            label: 'Expected QTY <i>(QTY Expected To Be Received)</i>',
            fieldname: 'verify_expected_qty',
            fieldtype: 'Int',
            read_only: 1 
        },
        {
            label: 'Received QTY <i>(QTY Already Counted)</i>',
            fieldname: 'verify_received_qty',
            fieldtype: 'Int',
            read_only: 1 
        },
        {
            label: '<b>Scan QTY</b> <i>(QTY Counted With This Scan)</i>',
            fieldname: 'verify_qty',
            fieldtype: 'Int',
            reqd: 1,
        },
        {
            label: '',
            fieldname: 'section_uom',
            fieldtype: 'Section Break',
        },
        {
            label: 'UOM',
            fieldname: 'verify_scan_uom',
            fieldtype: 'Link',
            options: 'UOM',
            read_only: 1 
        },
        {
            label: '',
            fieldname: 'column_break1',
            fieldtype: 'Column Break',
        },
        {
            label: '<b>UOM Conversion Factor</b>',
            fieldname: 'verify_conversion_factor',
            fieldtype: 'Int',
            reqd: 1,
            read_only: 1 
        },
        {
            label: '',
            fieldname: 'section_edit',
            fieldtype: 'Section Break',
        },
        {
            label: '<b>Edit Conversion Factor</b>',
            fieldname: 'change_conversion_factor',
            fieldtype: 'Button',
            click: function() {
                let field = d.fields_dict['verify_conversion_factor'];
                
                frappe.confirm(
                    'Selecting "Yes" will enable the editing of the Conversion Factor.<br>Selecting "No" will disable the editing of the Conversion Factor.<br><br>Are you certain you wish to proceed?',
                    () => {
                        field.df.read_only = 0;
                        field.refresh();
                    }, () => {
                        field.df.read_only = 1; 
                        field.refresh();
                    }
                );    
            }
        },
        {
            label: '',
            fieldname: 'column_break1',
            fieldtype: 'Column Break',
        },
        {
            label: '<b>Edit Expiration Dates</b>',
            fieldname: 'edit_expiration_dates',
            fieldtype: 'Button',
            click: function() {
                let item_code = d.fields_dict['verify_item_code'].value;
                let item_name = d.fields_dict['verify_item_name'].value;

                frappe.call({
                    method: 'jollys_receiving.api.fetch_expiration_dates',
                    args: {
                        item_code: item_code
                    },
                    callback: (r) => {
                        if(r.message['status'] === 'success') {
                            d.hide(); // Hides verify dialog 
                            expiration_dates = r.message['expiration_dates'];
                            expiration_dialog = create_expiration_dates_dialog(expiration_dates, d, item_name, item_code);
                        } else {
                            frappe.show_alert({
                                message: r.message['message'],
                                indicator:'red'
                            }, 10);
                        }
                    }
                });
            }
        }],
        size: 'small',
        primary_action_label: '<b>Complete Scan</b>',
        primary_action(values) {
            check_condition(frm, values).then(result => {
                if(result === true){
                    frappe.confirm(
                        'Received QTY will exceed expected QTY.<br>Are you sure you want to proceed?',
                        () => {
                            update_row(frm, values, data);
                            d.hide();
                            frm.fields_dict['scan_code'].input.focus();
                        },
                        () => {
                            // Closes the confirmation dialog if 'no' is selected
                        }
                    );
                } else {
                    update_row(frm, values, data);
                    d.hide();
                    frm.fields_dict['scan_code'].input.focus();
                }
            }).catch(err => {
                console.log(err);
            })
        }
    });
    for (const fieldname in data) {
        if (data.hasOwnProperty(fieldname)) {
            d.set_value(fieldname, data[fieldname]);
        }
    }   
    // Makes change_conversion_factor button reddy.find('button[data-fieldname="change_conversion_factor"]').addClass('btn-danger');
    d.$body.find('button[data-fieldname="change_conversion_factor"]').addClass('btn-danger');
    // Makes edit_expiration_dates button red
    d.$body.find('button[data-fieldname="edit_expiration_dates"]').addClass('btn-danger');
    
    d.show();
}

function create_expiration_dates_dialog(expiration_dates, verify_dialog, item_name, item_code) {
    let d = new frappe.ui.Dialog({
        title: '<b>Edit Expiration Dates</b>',
        fields: 
        [{
            label: 'Item Code',
            fieldname: 'expiration_item_code',
            fieldtype: 'Data',
            read_only: 1, 
            hidden: 1
        },
        {
            label: 'Expiration Dates',
            fieldname: 'expiration_dates_table',
            fieldtype: 'Table',
            data: expiration_dates,
            cannot_delete_rows: true,
            fields: [
                {
                    label: 'Expiration Date',
                    fieldname: 'expiration_date',
                    fieldtype: 'Date',
                    in_list_view: true,
                    reqd: 1
                }
            ]
        },
        {
            label: '',
            fieldname: 'section_cancel',
            fieldtype: 'Section Break',
        },
        {
            label: '<b>Cancel Edit</b>',
            fieldname: 'cancel_edit',
            fieldtype: 'Button',
            click: function() {
                d.hide(); // Hides expiration date dialog
                verify_dialog.show(); // Shows verify dialog
            }
        }],
        size: 'small',
        primary_action_label: '<b>Update Expiration Dates</b>',
        primary_action(values) {
            frappe.confirm(
                `These expiration dates will be set for item<br><br>${item_name}<br><br>Are you sure you want to proceed?`,
                () => {
                    frappe.call({
                        method: 'jollys_receiving.api.update_expiration_dates',
                        args: {
                            item_code: values['expiration_item_code'],
                            expiration_dates: values['expiration_dates_table']
                        },
                        callback: (r) => {
                            if(r.message['status'] === 'success') {
                                frappe.show_alert({
                                    message: r.message['message'],
                                    indicator:'green'
                                }, 5);
                            } else {
                                frappe.show_alert({
                                    message: r.message['message'],
                                    indicator:'red'
                                }, 10);
                            }
                        }
                    })

                    d.hide(); // Hides expiration date dialog
                    verify_dialog.show(); // Shows verify dialog
                },
                () => {
                    // Closes the confirmation dialog if 'no' is selected
                }
            );
        }
    });
    d.set_value('expiration_item_code', item_code);
    // Makes cancel_edit button red
    d.$body.find('button[data-fieldname="cancel_edit"]').addClass('btn-danger');
    d.show();
}

cur_frm.cscript['Stock Entry'] = function() {
    frappe.model.open_mapped_doc({
        method: 'jollys_receiving.api.create_stock_entry',
		frm: cur_frm
	});
};

cur_frm.cscript['Material Request'] = function() {
    frappe.model.open_mapped_doc({
        method: 'jollys_receiving.api.create_material_request',
		frm: cur_frm
	});
};

cur_frm.cscript['Purchase Order'] = function() {
    frappe.model.open_mapped_doc({
        method: 'jollys_receiving.api.create_purchase_order',
		frm: cur_frm
	});
};