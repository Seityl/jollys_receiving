// Copyright (c) 2024, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Audit", {
	refresh: function(frm) {
        // if(frm.is_new()) {
        //     frappe.call({
        //         method: 'jollys_receiving.jollys_receiving.doctype.stock_audit.stock_audit.StockAudit.get_item_bins_data',
        //         freeze: true,
        //         freeze_message: 'Fetching Bin Locations...',
        //         args: {
        //             item_code: 'JP53814'                
        //         },
        //         callback: (r) => {
        //             console.log(r.message)
        //         }
        //     });
        // }
	},
}); 
