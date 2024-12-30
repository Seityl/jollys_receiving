// frappe.listview_settings['Item'] = {
//     onload: function (listview) {
//         var df = {
//             fieldname: 'barcode',
//             label: 'Barcode',
//             fieldtype: 'Link',
//             options: 'Item Barcode',
//             ignore_user_permissions: true,
//             onchange: function() {
//                 var barcode = df.get_value(); // Get the selected barcode value
//                 if (barcode) {
//                     // Apply the filter to the listview
//                     listview.filters['barcode'] = barcode;
//                 } else {
//                     // Remove the filter if no barcode is selected
//                     delete listview.filters['barcode'];
//                 }
//                 listview.start = 0;
//                 listview.refresh();
//                 listview.on_filter_change(); // Trigger filter change
//             },
//         }
//         listview.page.add_field(df);
//     }
// };