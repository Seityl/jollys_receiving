app_name = "jollys_receiving"
app_title = "Jollys Receiving"
app_publisher = "Jollys Pharmacy"
app_description = "App for verifying receivings at Jollys Pharmacy."
app_email = "cdgrant@jollysonline.com"
app_license = "mit"

# required_apps = []

# Includes in <head>
# ------------------

fixtures = [
    {"dt":"Custom Field","filters":[["name","in",(
        "Stock Entry-custom_reference_receiving",
        "Material Request-reference_receiving",
        "Purchase Order-reference_receiving",
        "Purchase Receipt-reference_receiving",
        "Item-custom_bulk_list"
    )]]}
]

# include js, css files in header of desk.html
# app_include_css = "/assets/jollys_receiving/css/jollys_receiving.css"
# app_include_js = "/assets/jollys_receiving/js/jollys_receiving.js"

# include js, css files in header of web template
# web_include_css = "/assets/jollys_receiving/css/jollys_receiving.css"
# web_include_js = "/assets/jollys_receiving/js/jollys_receiving.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "jollys_receiving/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views

doctype_js = {
    "Item" : "public/js/custom_Item.js",
    "Stock Entry" : "public/js/custom_Stock Entry.js",
    "Sales Order" : "public/js/custom_Sales Order.js",
    "Purchase Order" : "public/js/custom_Purchase Order.js",
    "Purchase Receipt" : "public/js/custom_Purchase Receipt.js",
    "Material Request" : "public/js/custom_Material Request.js"
}

# doctype_list_js = {
#     "Material Request" : "public/js/custom_Material Request_list.js",
#     "Item" : "public/js/custom_item_list.js"
# }

# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "jollys_receiving/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "jollys_receiving.utils.jinja_methods",
# 	"filters": "jollys_receiving.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "jollys_receiving.install.before_install"
# after_install = "jollys_receiving.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "jollys_receiving.uninstall.before_uninstall"
# after_uninstall = "jollys_receiving.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "jollys_receiving.utils.before_app_install"
# after_app_install = "jollys_receiving.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "jollys_receiving.utils.before_app_uninstall"
# after_app_uninstall = "jollys_receiving.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "jollys_receiving.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "jollys_receiving.api.on_update",
# 		# "on_cancel": "method",
# 		# "on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"jollys_receiving.tasks.all"
# 	],
# 	"daily": [
# 		"jollys_receiving.tasks.daily"
# 	],
# 	"hourly": [
# 		"jollys_receiving.tasks.hourly"
# 	],
# 	"weekly": [
# 		"jollys_receiving.tasks.weekly"
# 	],
# 	"monthly": [
# 		"jollys_receiving.tasks.monthly"
# 	],
    'cron': {
        '0 7 * * *': [
            'jollys_receiving.public.set_picklists.schedule_set_picklists'
        ]
    }
}

# Testing
# -------

# before_tests = "jollys_receiving.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "jollys_receiving.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "jollys_receiving.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["jollys_receiving.utils.before_request"]
# after_request = ["jollys_receiving.utils.after_request"]

# Job Events
# ----------
# before_job = ["jollys_receiving.utils.before_job"]
# after_job = ["jollys_receiving.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"jollys_receiving.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }