# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
    return {
        "fieldname": "stock_audit",
        "internal_links": {
            "Item": "item_code",
            "Putaway Rule": ["warehouses", "reference_putaway_rule"],
            "Stock Entry": ["warehouses", "reference_stock_entry"],
        },
        "transactions": [
            { 
				# "label": _("Connected Documents"),
                "items": [
                    "Item",
                    "Putaway Rule",
                    "Stock Entry"
                ],
            },
        ],
    } 