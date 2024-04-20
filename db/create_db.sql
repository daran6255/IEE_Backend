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
    availableCredits INT DEFAULT 0
);

CREATE TABLE credits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userId VARCHAR(36) NOT NULL,
    creditsBought INT NOT NULL,
    amountPaid DECIMAL(10, 2) NOT NULL,
    paymentStatus BOOLEAN DEFAULT 0,
    paymentDate TIMESTAMP,
    createdDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (userId) REFERENCES user_info(id)
);

DESCRIBE user_info;
DESCRIBE credits;