// Copyright (c) 2024, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Receiving', {
    onload: function(frm) {
        if(frm.doc.scan_code) {
            frm.set_value('scan_code','');
        }
    },

    refresh: function(frm) {
        // Add Stock Entry button under Create if document is submitted
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(
                __('Stock Entry'),
                frm.cscript['Stock Entry'],
                __('Create')
            );
            frm.page.set_inner_btn_group_as_primary(__('Create'));
            // Hide verify scan checkbox when document is submitted
            frm.fields_dict['verify_scan'].df.hidden = true;
            frm.refresh_field('verify_scan');
        }
    },

    scan_code: function(frm) {
        scan_barcode(frm);   
    },

    verify_scan: function(frm) {
        if(frm.is_dirty()) {
            frm.save().then(() => {
                frm.reload_doc();
            });
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
            receipt_audit_name: frm.doc.name
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
                    }, 5);
                }
            } else if(!r.message['data']) {
                frappe.show_alert({
                    message: r.message['message'],
                    indicator:'red'
                }, 5);
            }
            frm.reload_doc();
        }
    })
}

function update_verified_item(frm) {
    // Fetch item data from table and create scan details dialog
    frappe.call({
        method: 'jollys_receiving.api.fetch_item_data',
        args: {
            receipt_audit_name: frm.doc.name
        },
        callback: (r) => {
            if(r.message['status'] === 'success') {
                data = {
                    'verify_barcode': r.message['verify_barcode'],
                    'verify_item_code': r.message['verify_item_code'],
                    'verify_item_name': r.message['verify_item_name'],
                    'verify_expected_qty': r.message['verify_expected_qty'],
                    'verify_qty': r.message['verify_qty'],
                    'verify_scan_uom': r.message['verify_scan_uom'],
                    'verify_conversion_factor': r.message['verify_conversion_factor']
                };        
                dialog = create_verify_dialogue(data, frm);
            } else {
                frappe.show_alert({
                    message: r.message['message'],
                    indicator:'red'
                }, 5);
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
                receipt_audit_name: frm.doc.name,
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
            receipt_audit_name: frm.doc.name,
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

                if(values['verify_conversion_factor'] != data['verify_conversion_factor']){
                    frappe.call({
                        method: 'jollys_receiving.api.update_item_uom_conversion_factor',
                        args: {
                            receipt_audit_name: frm.doc.name,
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
                                        receipt_audit_name: frm.doc.name,
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
                }, 5);
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
            label: '<b>Item Code</b>',
            fieldname: 'verify_item_code',
            fieldtype: 'Data',
            read_only: 1, 
            hidden: 1
        },
        {
            label: '<b>Item Code / Name</b>',
            fieldname: 'verify_item_name',
            fieldtype: 'Data',
            read_only: 1, 
        },
        {
            label: '<b>Expected QTY</b> <i>(Total Count Expected To Be Received)</i>',
            fieldname: 'verify_expected_qty',
            fieldtype: 'Int',
            read_only: 1 
        },
        {
            label: '<b>Scan QTY</b> <i>(Count Received With This Scan)</i>',
            fieldname: 'verify_qty',
            fieldtype: 'Int',
            reqd: 1,
        },
        {
            label: '<b>UOM</b>',
            fieldname: 'verify_scan_uom',
            fieldtype: 'Link',
            options: 'UOM',
            read_only: 1 
        },
        {
            label: '<b>UOM Conversion Factor</b>',
            fieldname: 'verify_conversion_factor',
            fieldtype: 'Int',
            reqd: 1,
            read_only: 1 
        },
        {
            label: '<b>Edit Conversion Factor</b>',
            fieldname: 'change_conversion_factor',
            fieldtype: 'Button',
            click: function(){
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
                        },
                        () => {
                            // Closes the confirmation dialog if 'no' is selected
                        }
                    );
                } else {
                    update_row(frm, values, data);
                    d.hide();
                }
            }).catch(err => {
                console.log(err)
            })
        }
    });
    for (const fieldname in data) {
        if (data.hasOwnProperty(fieldname)) {
            d.set_value(fieldname, data[fieldname]);
        }
    }   
    // Makes change_conversion_factor button red
    d.$body.find('button[data-fieldname="change_conversion_factor"]').addClass('btn-danger');
    d.show();
}

cur_frm.cscript['Stock Entry'] = function() {
    frappe.model.open_mapped_doc({
        method: 'jollys_receiving.api.create_stock_entry',
		frm: cur_frm
	});
};