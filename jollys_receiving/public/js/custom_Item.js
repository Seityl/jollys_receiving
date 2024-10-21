frappe.ui.form.on('Item', {
    after_save: function(frm) {
        frappe.call({
            method: 'jollys_receiving.public.py.custom_Item.update_bulk_item',
            args: {
                item_code: frm.doc.name
            },
        });
    }
});