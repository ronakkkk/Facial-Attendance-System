--
-- File generated with SQLiteStudio v3.2.1 on Mon Jan 10 04:41:34 2022
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: alerts
CREATE TABLE alerts (
    alertid  INTEGER       PRIMARY KEY AUTOINCREMENT,
    empid    VARCHAR,
    datetime DATETIME,
    date     DATE,
    location VARCHAR (100) 
);


-- Table: attendance_log
CREATE TABLE attendance_log (
    empid            VARCHAR       NOT NULL,
    intime           DATETIME      NOT NULL,
    outtime          DATETIME      NOT NULL,
    date             DATE          NOT NULL,
    firstlocation    VARCHAR (100) NOT NULL,
    lastseenlocation VARCHAR (100) NOT NULL
);


-- Table: category
CREATE TABLE category (
    name    VARCHAR NOT NULL
                    PRIMARY KEY
                    UNIQUE,
    cattype VARCHAR NOT NULL
);


-- Table: department
CREATE TABLE department (
    deptid    INTEGER  NOT NULL
                       PRIMARY KEY AUTOINCREMENT,
    location  VARCHAR  NOT NULL
                       REFERENCES locations (location),
    deptname  VARCHAR  NOT NULL,
    depthod   VARCHAR  NOT NULL,
    timestamp DATETIME NOT NULL
);


-- Table: holiday
CREATE TABLE holiday (
    date   DATE    NOT NULL,
    name   VARCHAR NOT NULL,
    htype  VARCHAR NOT NULL
                   REFERENCES category (name) 
                   DEFAULT NULL,
    deptid INTEGER REFERENCES department (deptid) 
                   DEFAULT NULL,
    PRIMARY KEY (
        date,
        name,
        htype,
        deptid
    )
);


-- Table: locations
CREATE TABLE locations (
    location     VARCHAR PRIMARY KEY,
    locationname VARCHAR NOT NULL
);


-- Table: person_details
CREATE TABLE person_details (
    empid          VARCHAR (100) PRIMARY KEY,
    name           VARCHAR (100) NOT NULL,
    empstatus      VARCHAR       NOT NULL
                                 REFERENCES category (name),
    currdept       INTEGER       REFERENCES department (deptid) 
                                 NOT NULL,
    currshift      VARCHAR       REFERENCES roster (rid) 
                                 NOT NULL,
    location       VARCHAR       REFERENCES locations (location) 
                                 NOT NULL,
    depttimestamp  DATETIME      NOT NULL,
    shifttimestamp DATETIME      NOT NULL
                                 DEFAULT NULL
);


-- Table: roster
CREATE TABLE roster (
    rid       VARCHAR PRIMARY KEY,
    name      VARCHAR UNIQUE
                      NOT NULL,
    starttime INTEGER NOT NULL,
    endtime   INTEGER NOT NULL,
    offday    VARCHAR NOT NULL
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
