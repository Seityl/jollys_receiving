// Copyright (c) 2025, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Auto Reorder Settings", {
	refresh: function(frm) {
        frm.add_custom_button('Generate Auto Reorders', function() {
            frappe.confirm(
                'Are you sure you wish to enqueue the generation of material requests based on current item reorder levels and quantities in the selected locations?',
                () => {
                    frappe.call({
                        method: 'jollys_receiving.public.set_picklists.schedule_set_picklists',
                        freeze: true,
                        freeze_message: 'Enqueuing...',
                        callback: (r) => {
                            if(r.message['status']) {
                                frappe.show_alert({
                                    message: 'Enqueued the generation of material requests based on current item reorder levels and quantities in the selected locations.',
                                    indicator:'green'
                                }, 10);
                            } else {
                                frappe.show_alert({
                                    message: `Something went wrong: ${r.message['message']}`,
                                    indicator:'red'
                                }, 10);
                            }
                        }
                    });
                    
                },
                () => {
                    // Closes the confirmation dialog if 'no' is selected
                }
            );
        });
	},
});