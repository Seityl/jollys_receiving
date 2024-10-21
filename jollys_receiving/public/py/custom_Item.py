import frappe 

@frappe.whitelist()
def update_bulk_item(item_code):
    self = frappe.get_doc('Item', item_code)

    if(self.custom_bulk_list):
        reorders = self.reorder_levels

        for reorder in reorders:
            if reorder.warehouse_group == 'MEGA Store - JP' and reorder.warehouse == 'Mega Retail - JP':
                self.remove(reorder)
                self.add_comment('Info', 'Bulk Stock Enabled: Removed Reorder Level & Qty for Mega Retail - JP')
                break

        self.save()            