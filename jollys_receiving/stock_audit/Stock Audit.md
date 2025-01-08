### **Purpose**

The **Stock Audit** app helps to make stock checks across warehouses simple and accurate. It reduces the effort needed by staff by handling complex processes automatically. Staff can use it to:

1. Count stock easily.
2. Update item details like names, descriptions, expiration dates, barcodes, supplier numbers, and units of measure (UOMs).

---
## **How It Works**

### 1. **Creating a Stock Audit**

- Go to the **Stock Audit List** and click **New Stock Audit**.
- Select the **location** (warehouse or store) where you will do the stock count. 
- **Search or Scan**:
    - Look up the item in the system by name or scan its barcode.
    - If the barcode doesn’t match any item, the app will show an error.
    - After saving the app fetches the latest information about the item including:
        - Name, description, expiration dates, barcodes, supplier numbers, stock levels, and UOMs.
	    - Any putaway rules for the bins (storage areas) are also linked automatically.
### 2. **Automatic Checks During the Audit**

- **Warehouse Capacity Check On Save**:
    - Makes sure that the stock in a warehouse doesn’t exceed its capacity.
    - If there’s too much stock, the app will show an error.
    
- **Priority Check On Save**:
    - Ensures that warehouse priorities are set correctly:
        - Priority must be at least 1.
        - No two warehouses can have the same priority.
    - The app shows an error if these rules are broken.

- **Posting Date and Time On Save:**
	- When you save the audit, the app automatically updates the **posting time** to the current time.
	- If you choose to modify the posting date or time, these will remain and stock adjustments will be made at the selected date and time.	
	
- **ERP Stock Count Check Before Submitting**:
    - The app compares the system’s stock count according to the document with the actual count in the bin.
    - If the counts don’t match, the app updates the system count of the document.
    - If an item is listed as stored in the warehouse but the count is 0, an error will appear.

### 3. **Submitting the Audit**

- The app:
    - Updates any changes to the item’s name, description, expiration dates, barcodes, supplier numbers, and UOMs.
    - Updates stock levels to match the audit.
    - For **KG Warehouse - JP**, it:
        - Creates or updates putaway rules based on warehouse settings.
        - Disables putaway rules for items not counted or stored in the warehouse.

---

### 6. **Canceling the Audit**

- If the audit is canceled:
    - The app undoes all changes made to the item.
    - Any stock transactions are reversed.
    - Putaway rules linked to the audit are disabled.

---
## **What the App Does Automatically**

### **1. Fetches Item Details**

When you add an item, the app automatically:

- Updates the item’s name, description, barcodes, UOMs, supplier numbers, and expiration dates.
- Links the bins (storage areas) and any related putaway rules.

---
### **2. Validates Warehouses**

The app checks that:

- The warehouse has enough capacity for the stock.
- Warehouse priorities are correctly set (no duplicate or invalid priorities).

---
### **3. Keeps ERP Stock Count Accurate**

The app ensures the document's ERP stock count matches the system count in the warehouse.

---
### **4. Manages Stock Levels**

- If the audit shows differences between the actual count and the system count, the app:
    - Creates stock transactions (receipts or transfers) to fix the differences.
    - Updates stock levels for all items in the audit.

---
### **5. Updates Putaway Rules**

- If the audit is for **KG Warehouse - JP**, the app:
    - Creates or updates putaway rules for warehouses based on capacity and priority.
    - Disables putaway rules for items not counted or stored in the warehouse.

---
### **6. Reverts Changes on Cancelation**

If the audit is canceled:
- Any changes to item details or stock levels are undone.
- Any putaway rules created or updated during the audit are disabled.

---
## **Key Benefits**

1. **Reduces Errors**:    
    - Ensures barcodes, stock counts, and warehouse details are accurate.
    
2. **Saves Time**:
    - Automatically fetches and updates item details.
    - Handles stock adjustments and putaway rules without manual work.
    
3. **Keeps Records Accurate**:
    - Keeps the system’s stock count in sync with actual stock levels.
    - Ensures all warehouses are correctly configured.

---

## **Common Scenarios**

### **1. Regular Stock Audits**

- Use the app to count and verify stock levels in warehouses or stores.

### **2. Updating Item Details**

- Modify item descriptions, barcodes, UOMs, and other details easily.

### **3. Fixing Stock Mismatches**

- Automatically adjust stock levels to match actual counts.

---