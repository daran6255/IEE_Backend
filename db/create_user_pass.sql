CREATE USER 'winvinaya_iee' @'localhost' IDENTIFIED BY 'wvi@iee123&';

CREATE DATABASE invoice_extraction;

SHOW DATABASES;

GRANT ALL PRIVILEGES ON invoice_extraction.* TO 'winvinaya_iee' @'localhost';

FLUSH PRIVILEGES;