CREATE DATABASE terratranslate;

USE terratranslate;

CREATE TABLE images_long (
    id INT AUTO_INCREMENT PRIMARY KEY,
    src_image LONGBLOB,
    gen_image LONGBLOB
);

CREATE TABLE userimages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userid INT NOT NULL,
    src_image LONGBLOB,
    gen_image LONGBLOB
);

SELECT * FROM userimages;

TRUNCATE TABLE userimages;

DROP TABLE userimages



CREATE TABLE accounts (
    userid INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    userpassword varchar(255) NOT NULL,
    email varchar(255) NOT NULL
);

SELECT * FROM accounts