CREATE DATABASE IF NOT EXISTS financial_analysis;

CREATE USER IF NOT EXISTS 'finance'@localhost IDENTIFIED BY 'finance-pass';

GRANT ALL PRIVILEGES ON financial_analysis.* TO 'finance'@localhost;