# Copyright (c) 2024, Jollys Pharmacy and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
    return {
        "fieldname": "receiving",
        "non_standard_fieldnames": {
            "Stock Entry": "custom_reference_receiving"
        },
        "internal_links": {
            "Purchase Receipt": ["items", "reference_purchase_receipt"],
            "Stock Entry": ["items", "custom_reference_receiving"]
        },
        "transactions": [
            { 
				"label": _("Related Documents"),
                "items": [
                    "Purchase Receipt",
					"Stock Entry"
                ],
            },
        ],
    }