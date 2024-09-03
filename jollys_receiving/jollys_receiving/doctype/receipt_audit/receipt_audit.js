// Copyright (c) 2024, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Receipt Audit", {
    refresh: function(frm) {
        // Add Stock Entry button under Create if document is submitted
        // if (frm.doc.docstatus == 1) {
        //     frm.add_custom_button(
        //         __("Stock Entry"),
        //         frm.cscript["Stock Entry"],
        //         __("Create")
        //     );

        //     frm.page.set_inner_btn_group_as_primary(__("Create"));
        // }
    },

    scan_code: function(frm) {
        scan_barcode(frm);   

    },

    verify_scan: function(frm) {
        if(frm.is_dirty()) {
            frm.save().then(() => {
                frm.reload_doc();
            })
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
            if(r.message['status'] === 'success') {
                frappe.show_alert({
                    message: r.message['message'],
                    indicator:'green'
                }, 5);

            } else {
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
    set_item_data_to_dialogue(frm);
}

function set_item_data_to_dialogue(frm) {
    frappe.call({
        method: 'jollys_receiving.api.fetch_item_data',
        args: {
            receipt_audit_name: frm.doc.name
            
        },
        callback: (r) => {
            data = {
                'verify_barcode': r.message['verify_barcode'],
                'verify_item_code': r.message['verify_item_code'],
                'verify_item_name': r.message['verify_item_name'],
                'verify_qty': r.message['verify_qty'],
                'verify_scan_uom': r.message['verify_scan_uom'],
                'verify_conversion_rate': r.message['verify_conversion_rate']
            };        
            
            dialog = create_verify_dialogue(data, frm);
        }
    });
}

function create_verify_dialogue(data, frm) {
    let d = new frappe.ui.Dialog({
        title: 'Scan Details',
        fields: 
        [{
            label: 'Barcode',
            fieldname: 'verify_barcode',
            fieldtype: 'Int',
            read_only: 1 
        },
        {
            label: 'Item Code',
            fieldname: 'verify_item_code',
            fieldtype: 'Data',
            read_only: 1 
        },
        {
            label: 'Item Name',
            fieldname: 'verify_item_name',
            fieldtype: 'Data',
            read_only: 1 
        },
        {
            label: 'Scan QTY',
            fieldname: 'verify_qty',
            fieldtype: 'Int',
            reqd: 1,
            read_only: 1 
        },
        {
            label: 'UOM',
            fieldname: 'verify_scan_uom',
            fieldtype: 'Link',
            options: 'UOM',
            read_only: 1 
        },
        {
            label: 'Conversion Factor',
            fieldname: 'verify_conversion_rate',
            fieldtype: 'Int',
            reqd: 1,
            read_only: 1 
        },
        {
            fieldtype: 'Section Break',
            fieldname: 'section_break_1'
        },
        {
            label: 'Edit Scan QTY',
            fieldname: "change_scan_qty",
            fieldtype: "Button",
            click: function(){
                let field = d.fields_dict['verify_qty'];
                frappe.confirm(
                    "Selecting 'Yes' will enable the editing of the Scan QTY.<br>Selecting 'No' will disable the editing of the Scan QTY.<br><br>Are you certain you wish to proceed?",
                    () => {
                        field.df.read_only = 0;
                        field.refresh();
                    }, () => {
                        field.df.read_only = 1; 
                        field.refresh();
                    }
                );
            }
        },{
            label: 'Edit Conversion Factor',
            fieldname: "change_conversion_factor",
            fieldtype: "Button",
            click: function(){
                let field = d.fields_dict['verify_conversion_rate'];
                frappe.confirm(
                    "Selecting 'Yes' will enable the editing of the Conversion Factor.<br>Selecting 'No' will disable the editing of the Conversion Factor.<br><br>Are you certain you wish to proceed?",
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
        primary_action_label: 'Complete Scan',
        primary_action(values) {
            frappe.call({
                method: 'jollys_receiving.api.update_verified_item',
                args: {
                    receipt_audit_name: frm.doc.name,
                    verify_item_code: values['verify_item_code'] || null,
                    verify_item_name: values['verify_item_name'] || null,
                    verify_qty: values['verify_qty'] || null,
                    verify_scan_uom: values['verify_scan_uom'] || null,
                    verify_conversion_rate: values['verify_conversion_rate'] || null
                    
                },
                callback: (r) => {
                    if(r.message['status'] === 'success') {
                        frappe.show_alert({
                            message: r.message['message'],
                            indicator:'green'
                        }, 5);
        
                        if(values['verify_conversion_rate'] != data['verify_conversion_rate']){
                            frappe.call({
                                method: 'jollys_receiving.api.update_item_uom_conversion_factor',
                                args: {
                                    receipt_audit_name: frm.doc.name,
                                    item_code: values['verify_item_code'],
                                    uom: values['verify_scan_uom'],
                                    conversion_rate: values['verify_conversion_rate']
                                    
                                },
                                callback: (r) => {
                                    if(r.message['status'] === 'success') {
                                        frappe.show_alert({
                                            message: r.message['message'],
                                            indicator:'green'
                                        }, 5);
                                        
                                    } else {
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
            
            d.hide();
        }
    });
    
    for (const fieldname in data) {
        if (data.hasOwnProperty(fieldname)) {
            d.set_value(fieldname, data[fieldname]);
            
        }
    }   
    d.show();
}

// cur_frm.cscript["Stock Entry"] = function() {
//     frappe.model.open_mapped_doc({
//         method: "jollys_receiving.api.create_stock_entry",
// 		frm: cur_frm
// 	});
// };