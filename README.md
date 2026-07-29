-#  Small Business Sales & Inventory Tracking System

## 📌 Abstract

The Small Business Sales and Inventory Tracking System automates sales recording and inventory management for local shop owners. It provides an interactive Python-based GUI connected to a MySQL database, allowing users to track daily transactions, automatically update stock levels, and analyze business performance using stored procedures, functions, and triggers.

---

## 🎯 Purpose of the Project

The goal of this project is to provide a user-friendly graphical interface for managing inventory and database operations without requiring users to write SQL queries manually.

This system enables users to:

* Manage customers, products, and orders efficiently
* Perform database operations through an intuitive GUI
* Reduce manual errors and improve productivity
* Access structured and reliable business data easily

It is designed especially for **small and medium-scale businesses** that need accurate inventory tracking without dealing with database complexity.

---

## Scope of the Project

This project involves developing a **Python GUI application (Tkinter)** integrated with a **MySQL relational database**.

### Key Capabilities:

* Perform full **CRUD operations** on:

  * Customer
  * Product
  * Orders
  * OrderItems

* Execute advanced database features:

  * Stored Procedures
  * Functions
  * Triggers
  * Nested Queries
  * Joins
  * Aggregate Queries

* Manage database users and permissions

---

## ⚙️ Features

### 🔹 1. CRUD Operations

Users can visually manage database records:

* Refresh Table View
* Insert new records
* Update records using primary keys
* Delete records
* Truncate tables
* Drop tables (with confirmation)

---

### 🔹 2. Advanced SQL Queries

Provides analytical insights using:

* **Nested Queries**

  * Customers with above-average spending
  * Products priced above average

* **Join Queries**

  * Customer + Sales data
  * OrderItems + Product details

* **Aggregate Queries**

  * Total sales per customer
  * Total quantity sold per product

---

### 🔹 3. Stored Procedures, Functions & Triggers

Automates business logic:

* Add new product with inventory
* Generate customer order summaries
* Calculate discounted price
* Evaluate stock status
* Auto-update inventory using triggers when orders are placed

---

### 🔹 4. User Privilege Management

Ensures secure database access:

* Create roles:

  * `inventory_admin`
  * `sales_user`
  * `viewer_user`

* Show user privileges

* Flush privileges

* List database users

---

## 🖥️ GUI Features

The system includes:

* Input forms for data entry
* Dropdown menus for table selection
* Output/result display panels
* Validation prompts
* Confirmation dialogs for critical actions

---

## 🧩 System Modules

### 1. CRUD Module

Handles basic database operations visually.

### 2. Query Module

Executes analytical SQL queries for insights.

### 3. Automation Module

Implements stored procedures, functions, and triggers.

### 4. Security Module

Manages database users and access control.

---

## 🛠️ Tech Stack

| Category  | Tools                  |
| --------- | ---------------------- |
| Database  | MySQL                  |
| Language  | Python 3               |
| GUI       | Tkinter, ttk           |
| Connector | mysql-connector-python |
| IDE       | VS Code / Python IDLE  |
| OS        | Windows, Linux         |

---

## Conclusion

This system simplifies inventory and sales management by combining a graphical interface with powerful database operations. It enhances efficiency, reduces errors, and provides meaningful business insights, making it ideal for small businesses.

---
