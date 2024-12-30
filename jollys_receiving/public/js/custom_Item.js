frappe.ui.form.on('Item', {
    // Filters UOMs in barcodes child table to only return values for item in row
    setup: function (frm) {
        frm.set_query("uom", "barcodes", function (doc, cdt, cdn) {
            let item_code = frm.doc.name;
            return {
                query: "jollys_receiving.api.get_item_uoms",
                filters: {
                    value: item_code,
                    apply_on: "Item Code",
                },
            };
        });
    },
    after_save: function(frm) {
        frappe.call({
            method: 'jollys_receiving.public.py.custom_Item.update_bulk_item',
            args: {
                item_code: frm.doc.name
            },
        });
    }
});