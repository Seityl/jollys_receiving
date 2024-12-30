# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class Receiving(Document):
    def before_insert(self):
        if not self.reference_purchase_receipt and not self.reference_purchase_order:
            frappe.throw(
                title = 'Alert',
                msg = _(f'Please get items from Purchase Receipt or Purchase Order')
            )

    def after_insert(self):
        self.attatch_invoice_from_reference_doc()

    def validate(self):
        self.update_per_received()

    def on_submit(self):
        self.validate_per_received()

    def attatch_invoice_from_reference_doc(self, attachments=None):
        if self.reference_purchase_receipt:
            attachments = frappe.get_all('File',
                filters={
                    'attached_to_doctype': 'Purchase Receipt',
                    'attached_to_name': self.reference_purchase_receipt
                }
            )

        if self.reference_purchase_order:
            attachments = frappe.get_all('File',
                filters={
                    'attached_to_doctype': 'Purchase Order',
                    'attached_to_name': self.reference_purchase_order
                }
            )

        if attachments:
            for attachment in attachments:
                invoice_doc = frappe.get_doc('File', attachment.name)

                invoice = frappe.get_doc({
                    "doctype": "File",
                    "file_name": invoice_doc.file_name,
                    "attached_to_doctype": self.doctype,
                    "attached_to_name": self.name,
                    "is_private": invoice_doc.is_private,
                    "content": invoice_doc.get_content()
                })

                invoice.insert()
        
    def validate_per_received(self):
        if(self.per_received > 100):
            frappe.msgprint(
                msg='Received % more than 100.',
                title='Alert',
                indicator='red'
            )

        elif(self.per_received < 100):
            frappe.msgprint(
                msg='Received % less than 100.',
                title='Alert',
                indicator='red'
            )

    def get_total_received_qty(self, total_received_qty=0):
        try:
            for row in self.items:
                row_received_qty = row.qty or 0
                total_received_qty += row_received_qty

            return total_received_qty
        
        except Exception as e:
            frappe.throw(f'Unexpected Error: {e}')

    def get_total_expected_qty(self, total_expected_qty=0):
        try:
            for row in self.items:
                row_expected_qty = row.expected_qty or 0
                total_expected_qty += row_expected_qty

            return total_expected_qty
        
        except Exception as e:
            frappe.throw(f'Unexpected Error: {e}')

    def update_per_received(self):
        try:
            total_expected_qty = self.get_total_expected_qty()
            total_received_qty = self.get_total_received_qty()

            if(total_expected_qty != 0 and total_received_qty != 0):
                per_received = (total_received_qty / total_expected_qty) * 100
                
                if(self.per_received != per_received):
                    self.per_received = per_received
                
            else:
                self.per_received = 0

        except Exception as e:
            frappe.throw(f'Unexpected Error: {e}')