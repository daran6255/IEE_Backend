CREATE USER 'winvinaya_iee' @'localhost' IDENTIFIED BY 'wvi@iee123&';

CREATE DATABASE invoice_extraction;

GRANT ALL PRIVILEGES ON invoice_extraction.* TO 'winvinaya_iee' @'localhost';

FLUSH PRIVILEGES;

USE invoice_extraction;

CREATE TABLE user_info (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(10) NOT NULL,
    company VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    verificationCode VARCHAR(255),
    verified BOOLEAN DEFAULT 0,
    availableCredits INT DEFAULT 0,
    totalCredits INT DEFAULT 0,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE credits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userId VARCHAR(36) NOT NULL,
    creditsBought INT NOT NULL,
    amountPaid DECIMAL(10, 2) NOT NULL,
    paymentStatus BOOLEAN DEFAULT 0,
    paymentDate TIMESTAMP,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    addedBy VARCHAR(10) NOT NULL,
    FOREIGN KEY (userId) REFERENCES user_info(id)
);

CREATE TABLE dashboard_stats (
    lockId INT NOT NULL DEFAULT 1,
    totalCustomers INT DEFAULT 0,
    totalCredits INT DEFAULT 0,
    usedCredits INT DEFAULT 0,
    totalInvoiceExtracted INT DEFAULT 0,
    totalAmount DECIMAL(10, 2) DEFAULT 0.00,
    PRIMARY KEY (lockId)
);

INSERT INTO
    dashboard_stats (lockId)
VALUES
    (1);

DESCRIBE user_info;

DESCRIBE credits;