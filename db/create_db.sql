CREATE USER 'winvinaya_iee' @'localhost' IDENTIFIED BY 'wvi@iee123&';

CREATE DATABASE invoice_extraction;

GRANT ALL PRIVILEGES ON invoice_extraction.* TO 'winvinaya_iee' @'localhost';

FLUSH PRIVILEGES;

USE invoice_extraction;

CREATE TABLE user_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(10) NOT NULL,
    company VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    verificationCode VARCHAR(255),
    verified BOOLEAN DEFAULT 0,
    available_credits INT DEFAULT 0
);

CREATE TABLE credits (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    User_id INT,
    FOREIGN KEY (User_id) REFERENCES user_info(id),
    credits_bought INT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount_paid DECIMAL(10, 2),
    payment_status BOOLEAN DEFAULT 0
);

DESCRIBE user_info;