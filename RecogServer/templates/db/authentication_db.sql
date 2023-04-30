--
-- File generated with SQLiteStudio v3.2.1 on Mon Jan 10 04:43:38 2022
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: login
CREATE TABLE login (
    username  VARCHAR (100) NOT NULL,
    timestamp DATETIME      NOT NULL,
    addr      VARCHAR (50)  NOT NULL,
    browser   VARCHAR       NOT NULL,
    remark    VARCHAR       NOT NULL
);


-- Table: user
CREATE TABLE user (
    username VARCHAR (100)  PRIMARY KEY,
    password VARCHAR (1000) NOT NULL,
    role     VARCHAR        NOT NULL,
    name     VARCHAR        NOT NULL
);

INSERT INTO user (username, password, role, name) VALUES ('admin', '21232f297a57a5a743894a0e4a801fc3', 'admin', 'admin');

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
