--
-- File generated with SQLiteStudio v3.2.1 on Mon Jan 10 04:43:11 2022
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: olddeptchange
CREATE TABLE olddeptchange (
    datetime DATETIME NOT NULL,
    deptid   VARCHAR  NOT NULL,
    deptname VARCHAR  NOT NULL,
    depthod  VARCHAR  NOT NULL,
    fromdate DATE     NOT NULL,
    todate   DATE     NOT NULL,
    location VARCHAR  NOT NULL
                      DEFAULT NULL,
    PRIMARY KEY (
        datetime,
        deptid
    )
);


-- Table: oldempdept
CREATE TABLE oldempdept (
    empid    VARCHAR  NOT NULL,
    datetime DATETIME NOT NULL,
    deptid   INTEGER  NOT NULL,
    deptname VARCHAR  NOT NULL,
    fromdate DATE     NOT NULL,
    todate   DATE     NOT NULL,
    depthod  VARCHAR  NOT NULL
                      DEFAULT NULL,
    location VARCHAR  NOT NULL
                      DEFAULT NULL,
    PRIMARY KEY (
        empid,
        datetime
    )
);


-- Table: oldempshifts
CREATE TABLE oldempshifts (
    empid     VARCHAR  NOT NULL,
    datetime  DATETIME NOT NULL,
    shift     VARCHAR  NOT NULL,
    starttime INTEGER  NOT NULL,
    endtime   INTEGER  NOT NULL,
    offday    VARCHAR  NOT NULL,
    fromdate  DATE     NOT NULL,
    todate    DATE     NOT NULL,
    shiftname VARCHAR  NOT NULL
                       DEFAULT NULL,
    PRIMARY KEY (
        empid,
        datetime
    )
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
