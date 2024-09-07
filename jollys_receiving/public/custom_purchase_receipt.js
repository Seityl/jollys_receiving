erpnext.stock.PurchaseReceiptController = class PurchaseReceiptController extends (
	erpnext.buying.BuyingController
) {
	refresh() {
        if (!this.frm.doc.is_return && this.frm.doc.status != "Closed") {
            if (this.frm.doc.docstatus == 1 && this.frm.doc.status != "Closed") {
                cur_frm.add_custom_button(
                    __("Make Receipt Audit"),
                    cur_frm.cscript["Make Receipt Audit"],
                    __("Create")
                );
            }
        }
    }
}

cur_frm.cscript["Make Receipt Audit"] = function () {
    frappe.model.open_mapped_doc({
        method: "jollys_receiving.api.make_receipt_audit",
        frm: cur_frm,
    });
};