// Filters UOMs in child table to only return values for item in row
frappe.ui.form.on('Stock Entry', {
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
});