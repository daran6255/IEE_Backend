CREATE USER 'winvinaya_iee' IDENTIFIED BY 'wvi@iee123&';

ALTER USER 'winvinaya_iee' @'localhost' IDENTIFIED BY 'wvi@iee123&';

CREATE DATABASE invoice_extraction;

SHOW DATABASES;

GRANT ALL PRIVILEGES ON invoice_extraction.* TO 'invoice_extraction' @'localhost';

FLUSH PRIVILEGES;