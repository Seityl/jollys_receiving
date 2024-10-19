frappe.ui.form.on('Purchase Order', {
	refresh(frm) {
		if(flt(frm.doc.per_received, 2) < 100) {
			frm.add_custom_button(__("Receiving"), () =>
				frappe.model.open_mapped_doc({
					method: "jollys_receiving.api.make_receiving_from_purchase_order",
					frm: cur_frm,
					}),
			__("Create"));
		}
	}
})