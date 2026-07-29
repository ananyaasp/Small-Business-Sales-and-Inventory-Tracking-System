CREATE DATABASE Inventory;
USE Inventory;

-- CUSTOMER TABLE
CREATE TABLE Customer (
    CustomerID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Address VARCHAR(255),
    LoyaltyPoints INT DEFAULT 0 CHECK (LoyaltyPoints >= 0)
);

-- SALES ORDER TABLE
CREATE TABLE SalesOrder (
    SalesID INT PRIMARY KEY,
    CustomerID INT NOT NULL,
    OrderDate DATE NOT NULL,
    TotalAmount DECIMAL(10,2) CHECK (TotalAmount >= 0),
    TaxAmount DECIMAL(10,2) DEFAULT 0 CHECK (TaxAmount >= 0),
    PaymentMode VARCHAR(50) CHECK (PaymentMode IN ('Cash','Card','UPI','NetBanking')),
    Discount DECIMAL(10,2) DEFAULT 0 CHECK (Discount >= 0),
    CONSTRAINT fk_sales_customer FOREIGN KEY (CustomerID)
        REFERENCES Customer(CustomerID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- PRODUCT TABLE
	CREATE TABLE Product (
		ProductID INT PRIMARY KEY,
		ProductName VARCHAR(100) NOT NULL,
		Category VARCHAR(50),
		Brand VARCHAR(50),
		Description TEXT,
		ManufactureDate DATE,
		ExpiryDate DATE,
		UnitPrice DECIMAL(10,2) NOT NULL CHECK (UnitPrice >= 0)
	);

-- INVENTORY TABLE
CREATE TABLE Inventory (
    ProductNo INT NOT NULL,
    BatchNumber VARCHAR(20) NOT NULL,
    QuantityInStock INT CHECK (QuantityInStock >= 0),
    LastRestockedDate DATE,
    StorageLocation VARCHAR(100),
    UnitOfMeasure VARCHAR(20) DEFAULT 'pcs',
    PRIMARY KEY (ProductNo, BatchNumber),
    CONSTRAINT fk_inventory_product FOREIGN KEY (ProductNo)
        REFERENCES Product(ProductID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);



-- ORDER ITEMS TABLE
CREATE TABLE OrderItems (
    OrderNo INT NOT NULL,
    ProductID INT NOT NULL,
    SalesID INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    UnitPrice DECIMAL(10,2) NOT NULL CHECK (UnitPrice >= 0),
    Discount DECIMAL(10,2) DEFAULT 0 CHECK (Discount >= 0),
    Subtotal DECIMAL(10,2) GENERATED ALWAYS AS (Quantity * UnitPrice - Discount) STORED,
    PRIMARY KEY (OrderNo, ProductID),
    CONSTRAINT fk_orderitems_order FOREIGN KEY (SalesID)
        REFERENCES SalesOrder(SalesID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_orderitems_product FOREIGN KEY (ProductID)
        REFERENCES Product(ProductID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

INSERT INTO Customer (CustomerID, Name, PhoneNumber, Email, Address, LoyaltyPoints) VALUES
(1, 'Amit Mehra', '9876543210', 'amit.mehra@example.com', '123 Park Street, Mumbai', 50),
(2, 'Priya Singh', '9988776655', 'priya.singh@example.com', '45 Rose Avenue, Delhi', 120),
(3, 'Ravi Kumar', '9123456780', 'ravi.kumar@example.com', '78 MG Road, Bengaluru', 300),
(4, 'Sneha Patel', '9876512345', 'sneha.patel@example.com', '56 Green Lane, Ahmedabad', 80),
(5, 'Karan Joshi', '9001827364', 'karan.joshi@example.com', '23 Lotus Enclave, Pune', 40);

INSERT INTO Product (ProductID, ProductName, Category, Brand, Description, ManufactureDate, ExpiryDate, UnitPrice) VALUES
(101, 'Organic Basmati Rice', 'Grocery', 'NatureFresh', 'Premium long-grain rice', '2025-01-10', '2026-01-10', 90.00),
(102, 'Smart LED Bulb', 'Electronics', 'Philips', '16W Wi-Fi enabled LED', '2024-06-01', NULL, 450.00),
(103, 'Almonds (250g)', 'Grocery', 'NuttyDelight', 'Premium quality almonds', '2025-06-10', '2026-12-10', 195.00),
(104, 'Toothpaste', 'Personal Care', 'Colgate', '100ml toothpaste', '2025-04-10', '2027-04-10', 55.00),
(105, 'Stationery Set', 'Stationery', 'Camlin', '10-piece combo', '2025-02-10', NULL, 120.00);

INSERT INTO SalesOrder (SalesID, CustomerID, OrderDate, TotalAmount, TaxAmount, PaymentMode, Discount) VALUES
(1001, 1, '2025-09-01', 500.00, 25.00, 'Card', 20.00),
(1002, 3, '2025-09-05', 195.00, 10.00, 'Cash', 10.00),
(1003, 2, '2025-09-06', 90.00, 4.00, 'UPI', 0.00),
(1004, 4, '2025-09-08', 450.00, 18.00, 'NetBanking', 15.00),
(1005, 5, '2025-09-09', 175.00, 8.00, 'Card', 5.00);

INSERT INTO Inventory (ProductNo, BatchNumber, QuantityInStock, LastRestockedDate, StorageLocation, UnitOfMeasure) VALUES
(101, 'BATCH2301', 60, '2025-08-15', 'Warehouse-A', 'kg'),
(102, 'LED2024A', 25, '2025-08-12', 'Warehouse-B', 'pcs'),
(103, 'ALMD2025X', 100, '2025-09-01', 'Warehouse-A', 'g'),
(104, 'TP202504', 75, '2025-08-20', 'Warehouse-C', 'pcs'),
(105, 'STSET105', 45, '2025-09-06', 'Warehouse-D', 'set');

INSERT INTO OrderItems (OrderNo, ProductID, SalesID, Quantity, UnitPrice, Discount) VALUES
(1, 101, 1001, 2, 90.00, 5.00),
(2, 103, 1002, 1, 195.00, 10.00),
(3, 102, 1004, 1, 450.00, 0.00),
(4, 104, 1005, 3, 55.00, 5.00),
(5, 105, 1003, 1, 120.00, 0.00);

-- Trigger 1: Update Inventory After Sale--
DELIMITER $$

CREATE TRIGGER trg_update_inventory_after_sale
AFTER INSERT ON OrderItems
FOR EACH ROW
BEGIN
    UPDATE Inventory
    SET QuantityInStock = QuantityInStock - NEW.Quantity
    WHERE ProductNo = NEW.ProductID
    LIMIT 1;
END$$

DELIMITER ;

-- Trigger 2: Add Loyalty Points on New Order
DELIMITER $$

CREATE TRIGGER trg_add_loyalty_points
AFTER INSERT ON SalesOrder
FOR EACH ROW
BEGIN
    UPDATE Customer
    SET LoyaltyPoints = LoyaltyPoints + FLOOR(NEW.TotalAmount / 100)
    WHERE CustomerID = NEW.CustomerID;
END$$

DELIMITER ;

-- Procedure 1: Add New Product and Initial Inventory
DELIMITER $$
CREATE PROCEDURE AddNewProductWithInventory(
    IN p_ProductID INT,
    IN p_ProductName VARCHAR(100),
    IN p_Category VARCHAR(50),
    IN p_Brand VARCHAR(50),
    IN p_Description TEXT,
    IN p_ManufactureDate DATE,
    IN p_ExpiryDate DATE,
    IN p_UnitPrice DECIMAL(10,2),
    IN p_BatchNumber VARCHAR(20),
    IN p_Quantity INT,
    IN p_StorageLocation VARCHAR(100),
    IN p_UnitOfMeasure VARCHAR(20)
)
BEGIN
    INSERT INTO Product (ProductID, ProductName, Category, Brand, Description, ManufactureDate, ExpiryDate, UnitPrice)
    VALUES (p_ProductID, p_ProductName, p_Category, p_Brand, p_Description, p_ManufactureDate, p_ExpiryDate, p_UnitPrice);
    INSERT INTO Inventory (ProductNo, BatchNumber, QuantityInStock, LastRestockedDate, StorageLocation, UnitOfMeasure)
    VALUES (p_ProductID, p_BatchNumber, p_Quantity, CURDATE(), p_StorageLocation, p_UnitOfMeasure);
END$$

DELIMITER ;
CALL AddNewProductWithInventory(106, 'Hand Sanitizer', 'Personal Care', 'Dettol', '100ml bottle', '2025-05-10', '2027-05-10', 65.00, 'HS2025A', 100, 'Warehouse-E', 'pcs');

-- Procedure 2: Get Customer Order Summary
DELIMITER $$
CREATE PROCEDURE GetCustomerOrderSummary(IN p_CustomerID INT)
BEGIN
    SELECT s.SalesID, s.OrderDate, s.TotalAmount, s.PaymentMode, s.Discount,
           o.ProductID, p.ProductName, o.Quantity, o.Subtotal
    FROM SalesOrder s
    JOIN OrderItems o ON s.SalesID = o.SalesID
    JOIN Product p ON o.ProductID = p.ProductID
    WHERE s.CustomerID = p_CustomerID
    ORDER BY s.OrderDate DESC;
END$$
DELIMITER ;
CALL GetCustomerOrderSummary(1);

-- Function 1: Calculate Discounted Price
DELIMITER $$
CREATE FUNCTION fn_calculate_discounted_price(price DECIMAL(10,2), discount DECIMAL(10,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    RETURN price - discount;
END$$
DELIMITER ;

SELECT fn_calculate_discounted_price(450, 50) AS FinalPrice;

-- Function 2: Get Stock Status
DELIMITER $$
CREATE FUNCTION fn_get_stock_status(qty INT)
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    DECLARE status VARCHAR(20);
    IF qty < 20 THEN
        SET status = 'Low Stock';
    ELSE
        SET status = 'Sufficient';
    END IF;
    RETURN status;
END$$
DELIMITER ;
SELECT ProductNo, QuantityInStock, fn_get_stock_status(QuantityInStock) AS StockStatus
FROM Inventory;

-- Nested Query 1: Customers Who Spent More Than the Average Order Amount
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

-- Nested Query 2: Products With Price Higher Than the Average Product Price
SELECT ProductName, UnitPrice
FROM Product
WHERE UnitPrice > (
    SELECT AVG(UnitPrice)
    FROM Product
);

-- Join 1: Customer and Sales Details --
SELECT c.Name, s.SalesID, s.OrderDate, s.TotalAmount, s.PaymentMode
FROM Customer c
JOIN SalesOrder s ON c.CustomerID = s.CustomerID;

-- Join 2: Order Items With Product Details --
SELECT o.SalesID, p.ProductName, o.Quantity, o.Subtotal
FROM OrderItems o
JOIN Product p ON o.ProductID = p.ProductID;

-- Join 3: Customer, Order, and Product Together --
SELECT c.Name AS CustomerName, p.ProductName, o.Quantity, s.OrderDate, s.PaymentMode
FROM Customer c
JOIN SalesOrder s ON c.CustomerID = s.CustomerID
JOIN OrderItems o ON s.SalesID = o.SalesID
JOIN Product p ON o.ProductID = p.ProductID
ORDER BY s.OrderDate DESC;

-- Aggregate Query 1: Total Sales Per Customer
SELECT c.Name, SUM(s.TotalAmount) AS TotalSpent
FROM Customer c
JOIN SalesOrder s ON c.CustomerID = s.CustomerID
GROUP BY c.CustomerID
ORDER BY TotalSpent DESC;

-- Aggregate Query 2: Total Quantity Sold Per Product
SELECT p.ProductName, SUM(o.Quantity) AS TotalQuantitySold
FROM Product p
JOIN OrderItems o ON p.ProductID = o.ProductID
GROUP BY p.ProductID
ORDER BY TotalQuantitySold DESC;

-- USER AND PRIVILEGE MANAGEMENT --

-- Create Users
CREATE USER 'inventory_admin'@'localhost' IDENTIFIED BY 'Admin@123';
CREATE USER 'sales_user'@'localhost' IDENTIFIED BY 'Sales@123';
CREATE USER 'viewer_user'@'localhost' IDENTIFIED BY 'View@123';

-- Grant Privileges
-- Admin: Full access to the entire database
GRANT ALL PRIVILEGES ON Inventory.* TO 'inventory_admin'@'localhost' WITH GRANT OPTION;

-- Sales User: Can read and insert sales/orders but not delete or modify structure
GRANT SELECT, INSERT, UPDATE ON Inventory.SalesOrder TO 'sales_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON Inventory.OrderItems TO 'sales_user'@'localhost';

-- Viewer User: Read-only access to the entire database
GRANT SELECT ON Inventory.* TO 'viewer_user'@'localhost';

-- Apply Privilege Changes
FLUSH PRIVILEGES;

-- nested query to test (Find customers who have placed an order with TotalAmount greater than the average order amount.)
SELECT Name, CustomerID
FROM Customer
WHERE CustomerID IN (
    SELECT CustomerID
    FROM SalesOrder
    WHERE TotalAmount > (
        SELECT AVG(TotalAmount) 
        FROM SalesOrder
    )
);

-- join query (List all orders with customer name and order details.)
SELECT c.Name AS CustomerName, s.SalesID, s.OrderDate, s.TotalAmount, s.PaymentMode
FROM SalesOrder s
JOIN Customer c ON s.CustomerID = c.CustomerID;

-- aggregate query (Get total quantity sold per product.)
SELECT p.ProductName, SUM(o.Quantity) AS TotalQuantitySold
FROM Product p
JOIN OrderItems o ON p.ProductID = o.ProductID
GROUP BY p.ProductID, p.ProductName
ORDER BY TotalQuantitySold DESC;
