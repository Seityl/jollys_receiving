// Copyright (c) 2025, Jollys Pharmacy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Auto Reorder Settings", {
	onload: function(frm) {
        // Hides Add Row button from schedule child table
        frm.get_field('schedule').grid.cannot_add_rows = true;
        // Hides Delete button from schedule child table
        frm.set_df_property('schedule', 'cannot_delete_rows', 1);
        // Hides Add Row button from locations child table
        frm.get_field('locations').grid.cannot_add_rows = true;
        // Hides Delete button from locations child table
        frm.set_df_property('locations', 'cannot_delete_rows', 1);
    },

	refresh: function(frm) {
        $('div[class="col grid-static-col d-flex justify-content-center"]').remove();
        $('div[class="col"]').remove();
        $('.btn-open-row').hide();
        $('.row-check').hide();

        frm.add_custom_button('Generate Auto Reorders', function() {
            frappe.confirm(
                'Are you sure you wish to enqueue the generation of material requests based on current item reorder levels and quantities in the selected locations?',
                () => {
                    frappe.call({
                        method: 'jollys_receiving.public.set_picklists.schedule_generate_auto_reorder_material_requests',
                        freeze: true,
                        freeze_message: 'Enqueuing...',
                        callback: (r) => {
                            if(!r.exc) {
                                frappe.show_alert({
                                    message: 'Enqueued the generation of material requests based on current item reorder levels and quantities in the selected locations.',
                                    indicator:'green'
                                }, 10);
                            } else {
                                frappe.show_alert({
                                    message: `Something went wrong: ${r.exc}`,
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