frappe.ui.form.on('Purchase Order', {
	refresh: function (frm) {
		if(frm.doc.docstatus == 0) {
			frm.add_custom_button(__("Receiving"), () =>
				frappe.model.open_mapped_doc({
					method: "jollys_receiving.api.make_receiving_from_purchase_order",
					frm: cur_frm,
					}),
			__("Create"));
		}
	},
    setup: function (frm) {
        frm.set_query("uom", "items", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                query: "jollys_receiving.api.get_item_uoms",
                filters: {
                    value: row.item_code,
                    apply_on: "Item Code",
                },
            };
        });
    },
})