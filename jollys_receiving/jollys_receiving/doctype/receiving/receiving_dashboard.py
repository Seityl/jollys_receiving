# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
    return {
        "fieldname": "receiving",
        "non_standard_fieldnames": {
            "Stock Entry": "custom_reference_receiving",
            "Material Request": "custom_reference_receiving",
            "Purchase Order": "custom_reference_receiving",
            "Customs Entry": "name"
        },
        "internal_links": {
            "Purchase Receipt": ["items", "reference_purchase_receipt"],
            "Stock Entry": ["items", "custom_reference_receiving"],
            "Material Request": ["items", "custom_reference_receiving"],
            "Customs Entry": "customs_entry"
        },
        "transactions": [
            { 
				"label": _("Buying"),
                "items": [
                    "Purchase Order",
                    "Purchase Receipt",
                ],
            },
            {
				"label": _("Stock"),
                "items": [
					"Stock Entry",
					"Material Request",
                ],
            },
            {
				"label": _("Customs"),
                "items": [
                    "Customs Entry"
                ],
            }
        ],
    }