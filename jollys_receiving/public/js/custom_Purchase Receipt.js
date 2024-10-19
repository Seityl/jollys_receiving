frappe.ui.form.on('Purchase Receipt', {
	refresh(frm) {
	    if (frm.doc.docstatus === 1) {
	        frm.add_custom_button(__("Receiving"), () => {
            frappe.model.open_mapped_doc({
                method: "jollys_receiving.api.make_receiving_from_purchase_receipt",
                frm: cur_frm,
                });
		    }, __("Create"));
	    }
	}
})