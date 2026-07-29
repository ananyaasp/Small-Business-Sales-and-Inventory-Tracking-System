"""
pro-trial.py

Tkinter GUI with tabs (ttk.Notebook) implementing:
- CRUD for Customer, SalesOrder, Product, Inventory, OrderItems (all tables)
- Buttons to call stored procedures and functions
- Demo/trigger actions (insert to show triggers effect)
- Pre-built nested/join/aggregate queries
- Simple user creation / privilege display controls

Requirements:
- mysql-connector-python
- Inventory database created with the SQL you provided (triggers/procs/functions/sample data)
"""

import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import datetime

DB_CONFIG = {
    'host': 'localhost',
    'user': 'inventory_admin',   # change if needed
    'password': 'Admin@123',     # change if needed
    'database': 'Inventory'
}

TABLES = ['Customer', 'SalesOrder', 'Product', 'Inventory', 'OrderItems']

class InventoryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management - Full GUI (Rubric-ready)")
        self.root.geometry("1000x700")

        # Connect to DB
        try:
            self.conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            self.cursor = self.conn.cursor(buffered=True, dictionary=True)
        except Error as e:
            messagebox.showerror("DB Connection Error", f"Unable to connect: {e}")
            root.destroy()
            return

        # Notebook / Tabs
        self.nb = ttk.Notebook(root)
        self.nb.pack(fill='both', expand=True)

        self.tab_crud = ttk.Frame(self.nb)
        self.tab_adv = ttk.Frame(self.nb)
        self.tab_queries = ttk.Frame(self.nb)
        self.tab_users = ttk.Frame(self.nb)

        self.nb.add(self.tab_crud, text='CRUD')
        self.nb.add(self.tab_adv, text='Triggers / Procs / Functions')
        self.nb.add(self.tab_queries, text='Prebuilt Queries')
        self.nb.add(self.tab_users, text='Users & Privileges')

        # Output area (common)
        self.output = ScrolledText(root, height=10)
        self.output.pack(fill='x', padx=6, pady=6)

        self.setup_crud_tab()
        self.setup_adv_tab()
        self.setup_queries_tab()
        self.setup_users_tab()

        # Close protocol
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_table_display()  # populate initial view

    # -----------------------
    # Helper DB Utilities
    # -----------------------
    def run(self, sql, params=None, fetch=False):
        try:
            self.cursor.execute(sql, params or ())
            if fetch:
                rows = self.cursor.fetchall()
                return rows
            else:
                self.conn.commit()
                return None
        except Error as e:
            self.output_insert(f"SQL Error: {e}\nSQL: {sql}\n")
            raise

    def output_insert(self, text):
        self.output.insert(tk.END, text)
        self.output.see(tk.END)

    def get_columns(self, table):
        try:
            rows = self.run(f"DESCRIBE {table};", fetch=True)
            return [r['Field'] for r in rows]
        except:
            return []

    def get_primary_key(self, table):
        q = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME=%s AND CONSTRAINT_NAME='PRIMARY';
        """
        res = self.run(q, (table,), fetch=True)
        if res:
            return res[0]['COLUMN_NAME']
        return None

    # -----------------------
    # CRUD Tab
    # -----------------------
    def setup_crud_tab(self):
        frm = self.tab_crud

        left = ttk.Frame(frm)
        left.pack(side='left', fill='y', padx=6, pady=6)

        ttk.Label(left, text="Table:").pack(anchor='w')
        self.crud_table_var = tk.StringVar(value=TABLES[0])
        self.crud_table_cb = ttk.Combobox(left, values=TABLES, textvariable=self.crud_table_var, state='readonly')
        self.crud_table_cb.pack(fill='x')
        self.crud_table_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table_display())

        ttk.Button(left, text="Refresh Table View", command=self.refresh_table_display).pack(fill='x', pady=4)

        # Insert button
        ttk.Button(left, text="Insert Row (prompt fields)", command=self.insert_row_prompt).pack(fill='x', pady=4)
        ttk.Button(left, text="Update Row (by PK)", command=self.update_row_prompt).pack(fill='x', pady=4)
        ttk.Button(left, text="Delete Row (by PK)", command=self.delete_row_prompt).pack(fill='x', pady=4)

        # Full-table operations
        ttk.Separator(left).pack(fill='x', pady=6)
        ttk.Button(left, text="Truncate Table", command=self.truncate_table).pack(fill='x', pady=2)
        ttk.Button(left, text="Drop Table", command=self.drop_table_prompt).pack(fill='x', pady=2)

        # Table display on right
        right = ttk.Frame(frm)
        right.pack(side='left', fill='both', expand=True, padx=6, pady=6)

        self.tree = ttk.Treeview(right)
        self.tree.pack(fill='both', expand=True)
        self.tree_scroll = ttk.Scrollbar(right, orient='vertical', command=self.tree.yview)
        self.tree['yscrollcommand'] = self.tree_scroll.set
        self.tree_scroll.pack(side='right', fill='y')

    def refresh_table_display(self, event=None):
        table = self.crud_table_var.get()
        if not table:
            return
        cols = self.get_columns(table)
        # reset tree
        self.tree.delete(*self.tree.get_children())
        self.tree['columns'] = cols
        self.tree['show'] = 'headings'
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor='center')
        # fetch rows
        try:
            rows = self.run(f"SELECT * FROM {table};", fetch=True)
            for r in rows:
                vals = [r.get(col) for col in cols]
                self.tree.insert('', tk.END, values=vals)
            self.output_insert(f"Refreshed view for {table}: {len(rows)} rows.\n")
        except Exception as e:
            self.output_insert(f"Could not fetch {table}: {e}\n")

    def insert_row_prompt(self):
        table = self.crud_table_var.get()
        cols = self.get_columns(table)
        if not cols:
            messagebox.showwarning("No columns", "Could not get columns for table.")
            return

        # build a simple dialog sequence to get values (skips auto-generated columns if any)
        values = []
        for col in cols:
            val = simpledialog.askstring("Insert", f"Enter value for {table}.{col}:")
            if val is None:
                self.output_insert("Insert cancelled by user.\n")
                return
            if val == '':
                values.append(None)
            else:
                values.append(val)
        placeholders = ", ".join(["%s"] * len(cols))
        col_names = ", ".join(cols)
        q = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders});"
        try:
            self.run(q, tuple(values))
            self.output_insert(f"Inserted row into {table}.\n")
            self.refresh_table_display()
        except Exception:
            pass

    def update_row_prompt(self):
        table = self.crud_table_var.get()
        pk = self.get_primary_key(table)
        if not pk:
            messagebox.showerror("No PK", f"Table {table} has no primary key defined.")
            return
        pk_val = simpledialog.askstring("Update", f"Enter{pk} value to update:")
        if pk_val is None: return
        cols = self.get_columns(table)
        # choose column to set
        set_col = simpledialog.askstring("Update", f"Enter column to update (options: {', '.join(cols)}):")
        if set_col is None or set_col not in cols:
            messagebox.showinfo("Cancelled/Invalid", "Update cancelled or invalid column.")
            return
        set_val = simpledialog.askstring("Update", f"Enter new value for {set_col}:")
        if set_val is None:
            return
        q = f"UPDATE {table} SET {set_col} = %s WHERE {pk} = %s;"
        try:
            self.run(q, (set_val, pk_val))
            self.output_insert(f"Updated {table}.{set_col} for {pk}={pk_val}.\n")
            self.refresh_table_display()
        except Exception:
            pass

    def delete_row_prompt(self):
        table = self.crud_table_var.get()
        pk = self.get_primary_key(table)
        if not pk:
            messagebox.showerror("No PK", f"Table {table} has no primary key defined.")
            return
        pk_val = simpledialog.askstring("Delete", f"Enter {pk} value to delete:")
        if pk_val is None:
            return
        if not messagebox.askyesno("Confirm", f"Delete row with {pk} = {pk_val} from {table}?"):
            return
        q = f"DELETE FROM {table} WHERE {pk} = %s;"
        try:
            self.run(q, (pk_val,))
            self.output_insert(f"Deleted row from {table} where {pk}={pk_val}.\n")
            self.refresh_table_display()
        except Exception:
            pass

    def truncate_table(self):
        t = self.crud_table_var.get()
        if not messagebox.askyesno("Confirm", f"Delete all rows from {t}?"):
            return
        try:
            self.run(f"DELETE FROM {t};")
            self.output_insert(f"All rows deleted from {t}.\n")
            self.refresh_table_display()
        except Exception:
            pass

    def drop_table_prompt(self):
        t = self.crud_table_var.get()
        if not messagebox.askyesno("Confirm DROP", f"DROP TABLE {t}? This will delete structure and data. Continue?"):
            return
        try:
            self.run(f"DROP TABLE {t};")
            self.output_insert(f"Table {t} dropped.\n")
            # Remove from dropdown to avoid errors
            try:
                TABLES.remove(t)
            except:
                pass
            self.crud_table_cb['values'] = TABLES
            self.crud_table_var.set(TABLES[0] if TABLES else "")
            self.refresh_table_display()
        except Exception:
            pass

    # -----------------------
    # Advanced: triggers/procs/functions
    # -----------------------
    def setup_adv_tab(self):
        frm = self.tab_adv

        left = ttk.Frame(frm)
        left.pack(side='left', fill='y', padx=6, pady=6)

        ttk.Label(left, text="Stored Procedures / Functions").pack(anchor='w', pady=2)
        ttk.Button(left, text="Add New Product With Inventory", command=self.call_add_product_proc).pack(fill='x', pady=2)
        ttk.Button(left, text="Get Customer Order Summary", command=self.call_get_customer_summary).pack(fill='x', pady=2)
        ttk.Separator(left).pack(fill='x', pady=6)
        ttk.Label(left, text="Functions").pack(anchor='w', pady=2)
        ttk.Button(left, text="fn_calculate_discounted_price (prompt)", command=self.call_fn_discounted).pack(fill='x', pady=2)
        ttk.Button(left, text="fn_get_stock_status (show all inventory statuses)", command=self.call_fn_stock_status).pack(fill='x', pady=2)
        ttk.Separator(left).pack(fill='x', pady=6)
        ttk.Label(left, text="Triggers Demo").pack(anchor='w', pady=2)
        ttk.Button(left, text="Run Trigger Demo: Insert test order + items", command=self.triggers_demo).pack(fill='x', pady=2)
        ttk.Button(left, text="Show Triggers (list)", command=self.list_triggers).pack(fill='x', pady=2)

        # right shows any result table
        right = ttk.Frame(frm)
        right.pack(side='left', fill='both', expand=True, padx=6, pady=6)
        self.adv_tree = ttk.Treeview(right)
        self.adv_tree.pack(fill='both', expand=True)
        self.adv_scroll = ttk.Scrollbar(right, orient='vertical', command=self.adv_tree.yview)
        self.adv_tree['yscrollcommand'] = self.adv_scroll.set
        self.adv_scroll.pack(side='right', fill='y')

    def call_add_product_proc(self):
        # prompt values for procedure
        try:
            pid = int(simpledialog.askstring("Proc", "ProductID (int):"))
        except:
            self.output_insert("Cancelled or invalid ProductID.\n"); return
        pname = simpledialog.askstring("Proc", "ProductName:")
        category = simpledialog.askstring("Proc", "Category:")
        brand = simpledialog.askstring("Proc", "Brand:")
        desc = simpledialog.askstring("Proc", "Description:")
        mfd = simpledialog.askstring("Proc", "ManufactureDate (YYYY-MM-DD):")
        exp = simpledialog.askstring("Proc", "ExpiryDate (YYYY-MM-DD) or blank:")
        price = simpledialog.askstring("Proc", "UnitPrice (decimal):")
        batch = simpledialog.askstring("Proc", "BatchNumber:")
        qty = simpledialog.askstring("Proc", "Quantity (int):")
        location = simpledialog.askstring("Proc", "StorageLocation:")
        uom = simpledialog.askstring("Proc", "UnitOfMeasure (e.g., pcs):")
        if None in (pname, category, brand, desc, mfd, price, batch, qty, location, uom):
            self.output_insert("Procedure call cancelled.\n"); return
        try:
            self.run("CALL AddNewProductWithInventory(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",
                     (pid, pname, category, brand, desc, mfd if mfd!='' else None,
                      exp if exp!='' else None, price, batch, qty, location, uom))
            self.output_insert("Procedure AddNewProductWithInventory executed.\n")
            self.refresh_table_display()
        except Exception as e:
            self.output_insert(f"Procedure call error: {e}\n")

    def call_get_customer_summary(self):
        cid = simpledialog.askstring("GetCustomerOrderSummary", "Enter CustomerID:")
        if cid is None:
            return
        try:
            rows = self.run("CALL GetCustomerOrderSummary(%s);", (cid,), fetch=True)
            # show in adv_tree
            if rows is None:
                self.output_insert("Procedure executed (no rows)\n")
                return
            self.populate_adv_tree(rows)
            self.output_insert(f"GetCustomerOrderSummary returned {len(rows)} rows.\n")
        except Exception as e:
            # some MySQL drivers need to fetch multiple result sets — handle simply by selecting results after call:
            try:
                # attempt fallback: select via join
                q = """
                    SELECT s.SalesID, s.OrderDate, s.TotalAmount, s.PaymentMode, s.Discount,
                           o.ProductID, p.ProductName, o.Quantity, o.Subtotal
                    FROM SalesOrder s
                    JOIN OrderItems o ON s.SalesID = o.SalesID
                    JOIN Product p ON o.ProductID = p.ProductID
                    WHERE s.CustomerID = %s
                    ORDER BY s.OrderDate DESC;
                """
                rows = self.run(q, (cid,), fetch=True)
                self.populate_adv_tree(rows)
                self.output_insert(f"(Fallback) Got {len(rows)} rows.\n")
            except Exception as ex:
                self.output_insert(f"Error calling GetCustomerOrderSummary: {ex}\n")

    def call_fn_discounted(self):
        price = simpledialog.askstring("Function", "Enter price (decimal):")
        discount = simpledialog.askstring("Function", "Enter discount (decimal):")
        if price is None or discount is None:
            return
        try:
            rows = self.run("SELECT fn_calculate_discounted_price(%s,%s) AS FinalPrice;", (price, discount), fetch=True)
            if rows:
                self.output_insert(f"FinalPrice = {rows[0]['FinalPrice']}\n")
        except Exception as e:
            self.output_insert(f"Error calling function: {e}\n")

    def call_fn_stock_status(self):
        try:
            rows = self.run("SELECT ProductNo, QuantityInStock, fn_get_stock_status(QuantityInStock) AS StockStatus FROM Inventory;", fetch=True)
            self.populate_adv_tree(rows)
            self.output_insert(f"Stock status rows: {len(rows)}\n")
        except Exception as e:
            self.output_insert(f"Error: {e}\n")

    def triggers_demo(self):
        # This will insert a small SalesOrder and OrderItems to show triggers:
        try:
            # new SalesID: generate large unique id using timestamp
            sales_id = int(datetime.datetime.now().timestamp()) % 1000000 + 2000
            cust_id = simpledialog.askstring("Trigger Demo", "Enter CustomerID to credit loyalty points (existing):")
            if cust_id is None:
                return
            order_total = simpledialog.askstring("Trigger Demo", "Enter TotalAmount (decimal):", initialvalue="100.00")
            payment = simpledialog.askstring("Trigger Demo", "PaymentMode (Cash/Card/UPI/NetBanking):", initialvalue="Cash")
            # Insert sales order
            self.run("INSERT INTO SalesOrder (SalesID, CustomerID, OrderDate, TotalAmount, TaxAmount, PaymentMode, Discount) VALUES (%s,%s,%s,%s,%s,%s,%s);",
                     (sales_id, cust_id, datetime.date.today(), order_total, 0, payment, 0))
            # Insert one order item for product 101 or ask user
            prod = simpledialog.askstring("Trigger Demo", "ProductID for order item (existing product e.g., 101):", initialvalue="101")
            qty = simpledialog.askstring("Trigger Demo", "Quantity:", initialvalue="1")
            unitprice = self.run("SELECT UnitPrice FROM Product WHERE ProductID=%s;", (prod,), fetch=True)
            if not unitprice:
                messagebox.showwarning("No product", "Product not found.")
                return
            up = unitprice[0]['UnitPrice']
            # Insert order item; OrderNo could be a sequence, but use increment
            # find max OrderNo
            max_orderno = self.run("SELECT COALESCE(MAX(OrderNo),0) AS maxo FROM OrderItems;", fetch=True)[0]['maxo']
            new_orderno = max_orderno + 1
            self.run("INSERT INTO OrderItems (OrderNo, ProductID, SalesID, Quantity, UnitPrice, Discount) VALUES (%s,%s,%s,%s,%s,%s);",
                     (new_orderno, prod, sales_id, qty, up, 0))
            self.output_insert(f"Inserted SalesOrder {sales_id} and OrderItems {new_orderno} -> triggers should have adjusted Inventory and LoyaltyPoints.\n")
            # show updated inventory and customer loyalty
            inv = self.run("SELECT ProductNo, QuantityInStock FROM Inventory WHERE ProductNo=%s;", (prod,), fetch=True)
            cust = self.run("SELECT CustomerID, LoyaltyPoints FROM Customer WHERE CustomerID=%s;", (cust_id,), fetch=True)
            if inv: self.output_insert(f"Inventory after sale: {inv[0]}\n")
            if cust: self.output_insert(f"Customer after sale: {cust[0]}\n")
            self.refresh_table_display()
        except Exception as e:
            self.output_insert(f"Trigger demo error: {e}\n")

    def list_triggers(self):
        try:
            rows = self.run("SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE, ACTION_STATEMENT FROM INFORMATION_SCHEMA.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE();", fetch=True)
            self.populate_adv_tree(rows)
            self.output_insert(f"Found {len(rows)} triggers in DB.\n")
        except Exception as e:
            self.output_insert(f"Could not list triggers: {e}\n")

    def populate_adv_tree(self, rows):
        # generic populate for adv_tree
        self.adv_tree.delete(*self.adv_tree.get_children())
        if not rows:
            return
        cols = list(rows[0].keys())
        self.adv_tree['columns'] = cols
        self.adv_tree['show'] = 'headings'
        for c in cols:
            self.adv_tree.heading(c, text=c)
            self.adv_tree.column(c, width=140)
        for r in rows:
            vals = [r.get(c) for c in cols]
            self.adv_tree.insert('', tk.END, values=vals)

    # -----------------------
    # Prebuilt Queries Tab
    # -----------------------
    def setup_queries_tab(self):
        frm = self.tab_queries
        left = ttk.Frame(frm)
        left.pack(side='left', fill='y', padx=6, pady=6)

        ttk.Label(left, text="Nested / Join / Aggregate Queries").pack(anchor='w', pady=2)
        ttk.Button(left, text="Nested: Customers with avg order > overall avg", command=self.query_nested_customers).pack(fill='x', pady=2)
        ttk.Button(left, text="Nested: Products priced above avg", command=self.query_products_above_avg).pack(fill='x', pady=2)
        ttk.Separator(left).pack(fill='x', pady=6)
        ttk.Button(left, text="Join: Customer + Sales details", command=self.query_join_customer_sales).pack(fill='x', pady=2)
        ttk.Button(left, text="Join: OrderItems with Product details", command=self.query_join_orderitems).pack(fill='x', pady=2)
        ttk.Separator(left).pack(fill='x', pady=6)
        ttk.Button(left, text="Aggregate: Total Sales Per Customer", command=self.query_agg_sales_per_customer).pack(fill='x', pady=2)
        ttk.Button(left, text="Aggregate: Total Quantity Sold Per Product", command=self.query_agg_qty_per_product).pack(fill='x', pady=2)

        right = ttk.Frame(frm)
        right.pack(side='left', fill='both', expand=True, padx=6, pady=6)
        self.q_tree = ttk.Treeview(right)
        self.q_tree.pack(fill='both', expand=True)
        self.q_scroll = ttk.Scrollbar(right, orient='vertical', command=self.q_tree.yview)
        self.q_tree['yscrollcommand'] = self.q_scroll.set
        self.q_scroll.pack(side='right', fill='y')

    def show_query_rows(self, rows):
        self.q_tree.delete(*self.q_tree.get_children())
        if not rows:
            self.output_insert("Query returned no rows.\n")
            return
        cols = list(rows[0].keys())
        self.q_tree['columns'] = cols
        self.q_tree['show'] = 'headings'
        for c in cols:
            self.q_tree.heading(c, text=c)
            self.q_tree.column(c, width=160)
        for r in rows:
            vals = [r.get(c) for c in cols]
            self.q_tree.insert('', tk.END, values=vals)

    def query_nested_customers(self):
        q = """
            SELECT Name, CustomerID
            FROM Customer
            WHERE CustomerID IN (
                SELECT CustomerID
                FROM SalesOrder
                GROUP BY CustomerID
                HAVING AVG(TotalAmount) > (
                    SELECT AVG(TotalAmount) FROM SalesOrder
                )
            );
        """
        rows = self.run(q, fetch=True)
        self.show_query_rows(rows)
        self.output_insert(f"Nested query returned {len(rows)} rows.\n")

    def query_products_above_avg(self):
        q = "SELECT ProductName, UnitPrice FROM Product WHERE UnitPrice > (SELECT AVG(UnitPrice) FROM Product);"
        rows = self.run(q, fetch=True)
        self.show_query_rows(rows)
        self.output_insert(f"Products above avg price: {len(rows)}\n")

    def query_join_customer_sales(self):
        q = "SELECT c.Name, s.SalesID, s.OrderDate, s.TotalAmount, s.PaymentMode FROM Customer c JOIN SalesOrder s ON c.CustomerID = s.CustomerID;"
        rows = self.run(q, fetch=True)
        self.show_query_rows(rows)
        self.output_insert(f"Join returned {len(rows)} rows.\n")

    def query_join_orderitems(self):
        q = "SELECT o.SalesID, p.ProductName, o.Quantity, o.Subtotal FROM OrderItems o JOIN Product p ON o.ProductID = p.ProductID;"
        rows = self.run(q, fetch=True)
        self.show_query_rows(rows)
        self.output_insert(f"Join OrderItems returned {len(rows)} rows.\n")

    def query_agg_sales_per_customer(self):
        q = "SELECT c.Name, SUM(s.TotalAmount) AS TotalSpent FROM Customer c JOIN SalesOrder s ON c.CustomerID = s.CustomerID GROUP BY c.CustomerID ORDER BY TotalSpent DESC;"
        rows = self.run(q, fetch=True)
        self.show_query_rows(rows)
        self.output_insert(f"Aggregate rows: {len(rows)}\n")

    def query_agg_qty_per_product(self):
        q = "SELECT p.ProductName, SUM(o.Quantity) AS TotalQuantitySold FROM Product p JOIN OrderItems o ON p.ProductID = o.ProductID GROUP BY p.ProductID, p.ProductName ORDER BY TotalQuantitySold DESC;"
        rows = self.run(q, fetch=True)
        self.show_query_rows(rows)
        self.output_insert(f"Aggregate rows: {len(rows)}\n")

    # -----------------------
    # Users & Privileges Tab
    # -----------------------
    def setup_users_tab(self):
        frm = self.tab_users
        left = ttk.Frame(frm)
        left.pack(side='left', fill='y', padx=6, pady=6)
        ttk.Label(left, text="User Management").pack(anchor='w', pady=2)
        ttk.Button(left, text="Create users (inventory_admin/sales_user/viewer_user from SQL)", command=self.create_users_sample).pack(fill='x', pady=2)
        ttk.Button(left, text="Show Grants for a user", command=self.show_grants_prompt).pack(fill='x', pady=2)
        ttk.Button(left, text="Flush Privileges", command=self.flush_privileges).pack(fill='x', pady=2)
        ttk.Button(left, text="List DB Users", command=self.list_db_users).pack(fill='x', pady=2)

        right = ttk.Frame(frm)
        right.pack(side='left', fill='both', expand=True, padx=6, pady=6)
        self.users_tree = ttk.Treeview(right)
        self.users_tree.pack(fill='both', expand=True)
        self.users_scroll = ttk.Scrollbar(right, orient='vertical', command=self.users_tree.yview)
        self.users_tree['yscrollcommand'] = self.users_scroll.set
        self.users_scroll.pack(side='right', fill='y')

    def create_users_sample(self):
        # attempt to create sample users as SQL provided; ignore errors if they exist
        statements = [
            "CREATE USER IF NOT EXISTS 'inventory_admin'@'localhost' IDENTIFIED BY 'Admin@123';",
            "CREATE USER IF NOT EXISTS 'sales_user'@'localhost' IDENTIFIED BY 'Sales@123';",
            "CREATE USER IF NOT EXISTS 'viewer_user'@'localhost' IDENTIFIED BY 'View@123';",
            "GRANT ALL PRIVILEGES ON Inventory.* TO 'inventory_admin'@'localhost' WITH GRANT OPTION;",
            "GRANT SELECT, INSERT, UPDATE ON Inventory.SalesOrder TO 'sales_user'@'localhost';",
            "GRANT SELECT, INSERT, UPDATE ON Inventory.OrderItems TO 'sales_user'@'localhost';",
            "GRANT SELECT ON Inventory.* TO 'viewer_user'@'localhost';"
        ]
        try:
            for s in statements:
                try:
                    self.run(s)
                except Exception as e:
                    # continue on failure
                    self.output_insert(f"Ignoring user creation/grant error: {e}\n")
            self.output_insert("User creation / grant statements executed (errors ignored).\n")
            self.list_db_users()
        except Exception as e:
            self.output_insert(f"Error creating users: {e}\n")

    def show_grants_prompt(self):
        u = simpledialog.askstring("Show Grants", "Enter username@host (e.g., sales_user@localhost):")
        if u is None:
            return
        if '@' not in u:
            messagebox.showinfo("Format", "Provide format user@host.")
            return
        user, host = u.split('@', 1)
        try:
            res = self.run("SHOW GRANTS FOR %s@%s;" % (f"'{user}'", f"'{host}'"), fetch=True)
            # Note: some drivers return list of single dicts with keys like 'Grants for ...' or raw tuples; handle generically
            self.users_tree.delete(*self.users_tree.get_children())
            self.users_tree['columns'] = ['Grant']
            self.users_tree['show'] = 'headings'
            self.users_tree.heading('Grant', text='Grant')
            if res:
                # res may be list of dicts or tuples
                for r in res:
                    # if dict
                    if isinstance(r, dict):
                        vals = list(r.values())
                        g = vals[0]
                    else:
                        g = r[0]
                    self.users_tree.insert('', tk.END, values=(g,))
                self.output_insert(f"Displayed grants for {u}.\n")
            else:
                self.output_insert("No grants found or insufficient privileges to view.\n")
        except Exception as e:
            self.output_insert(f"Show grants error: {e}\n")

    def flush_privileges(self):
        try:
            self.run("FLUSH PRIVILEGES;")
            self.output_insert("FLUSH PRIVILEGES executed.\n")
        except Exception as e:
            self.output_insert(f"Error flushing privileges: {e}\n")

    def list_db_users(self):
        try:
            rows = self.run("SELECT User, Host FROM mysql.user;", fetch=True)
            self.users_tree.delete(*self.users_tree.get_children())
            self.users_tree['columns'] = ['User','Host']
            self.users_tree['show'] = 'headings'
            self.users_tree.heading('User', text='User')
            self.users_tree.heading('Host', text='Host')
            for r in rows:
                self.users_tree.insert('', tk.END, values=(r.get('User'), r.get('Host')))
            self.output_insert(f"Listed {len(rows)} DB users.\n")
        except Exception as e:
            self.output_insert(f"Could not list DB users: {e}\n")

    # -----------------------
    # Cleanup
    # -----------------------
    def on_close(self):
        try:
            if self.conn.is_connected():
                self.cursor.close()
                self.conn.close()
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryGUI(root)
    root.mainloop()
