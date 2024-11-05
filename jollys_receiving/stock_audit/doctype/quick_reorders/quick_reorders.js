// Copyright (c) 2024, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quick Reorders', {
    setup: (frm) => {
		frm.set_query('item_code', () => {
			if (!frm.doc.warehouse) {
				frm.trigger('check_warehouse');
			}
		});
	},

	refresh: (frm) => {
		frm.disable_save();
	},

	check_warehouse: (frm) => {
		frappe.msgprint(__('Please enter Warehouse'));
		frm.trigger('clear_fields');
	},
    
	warehouse: (frm) => {
        if (frm.doc.item_code || frm.doc.item_barcode) {
			frm.trigger('get_stock_and_item_details');
		}
	},
    
	item_code: (frm) => {
        frappe.flags.last_updated_element = 'item_code';
		frm.trigger('get_stock_and_item_details');
        if (frm.doc.item_code) {
            frm.fields_dict['qty'].df.hidden = false;
            frm.fields_dict['section_reorders'].df.hidden = false;
            frm.refresh();
        } else {
            frm.fields_dict['qty'].df.hidden = true;
            frm.fields_dict['section_reorders'].df.hidden = true;
            frm.refresh();
        }
	},
    
	item_barcode: (frm) => {
        frappe.flags.last_updated_element = 'item_barcode';
		frm.trigger('get_stock_and_item_details');
	},
    
    clear_fields: (frm) => {
        frm.doc.item_barcode = null;
        frm.doc.item_code = null;
        frm.doc.item_name = null;
        frm.doc.description = null;
        frm.doc.warehouse_reorder_level = null;
        frm.doc.warehouse_reorder_qty = null;
        frm.fields_dict['section_reorders'].df.hidden = true;
        frm.fields_dict['qty'].df.hidden = true;
        frm.refresh();
    },
    
	get_stock_and_item_details: (frm) => {
		if (!frm.doc.warehouse) {
            frm.trigger('check_warehouse');
		} else if (frm.doc.item_code || frm.doc.item_barcode) {
			let filters = {
				warehouse: frm.doc.warehouse,
			};
			if (frappe.flags.last_updated_element === 'item_code') {
				filters = { ...filters, ...{ item_code: frm.doc.item_code } };
			} else {
                filters = { ...filters, ...{ barcode: frm.doc.item_barcode } };
			}
			frappe.call({
                method: 'jollys_receiving.stock_audit.doctype.quick_reorders.quick_reorders.get_stock_and_item_details',
				args: filters,
				callback: (r) => {
					if (r.message) {
                        let fields = ['item_code', 'qty', 'item_name', 'description', 'warehouse_reorder_level', 'warehouse_reorder_qty'];
						if (!r.message['barcodes'].includes(frm.doc.item_barcode)) {
							frm.doc.item_barcode = '';
							frm.refresh();
						}
						fields.forEach(function (field) {
                            frm.set_value(field, r.message[field]);
						});
					} else {
                        frm.trigger('clear_fields')
                        frappe.show_alert({
                            message: 'Invalid Barcode. There is no Item attached to this barcode.',
                            indicator:'red'
                        }, 10);
                    }
				},
			});
		}
	},

    update_reorders: (frm) => {
        if (!frm.doc.warehouse) {
			frm.trigger('check_warehouse');
		} else if (frm.doc.item_code) {
            frappe.call({
                method: 'jollys_receiving.stock_audit.doctype.quick_reorders.quick_reorders.update_item_reorder',
				args: {
                    item_code: frm.doc.item_code,
                    warehouse: frm.doc.warehouse,
                    warehouse_reorder_level: frm.doc.warehouse_reorder_level,
                    warehouse_reorder_qty: frm.doc.warehouse_reorder_qty
                },
				callback: (r) => {
                    if (r.message) {
                        frappe.show_alert({
                            message: `Updated ${frm.doc.warehouse} Reorder for <a href="/app/item/${frm.doc.item_code}" target="_blank">${frm.doc.item_code}</a>`,
                            indicator:'green'
                        }, 10);
                        frm.trigger('clear_fields')
					} else {
                        frm.trigger('clear_fields')
                    }
				},
			});
		}
    }
});
