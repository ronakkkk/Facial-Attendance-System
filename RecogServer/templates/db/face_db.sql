--
-- File generated with SQLiteStudio v3.2.1 on Mon Jan 10 04:42:00 2022
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: identity
CREATE TABLE identity (
    empid VARCHAR PRIMARY KEY,
    entry STRING
);


-- Table: vectors
CREATE TABLE vectors (
    f_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    label  STRING  NOT NULL,
    empid  STRING  REFERENCES identity (empid) 
                   NOT NULL,
    vector BLOB    NOT NULL
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
