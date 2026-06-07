-- ============================================================
-- reset_db.sql  –  Drop and recreate all Zomerkamp tables
-- Run as: mysql -u zomerkamp_user -p zomerkamp < reset_db.sql
--         or paste into your MySQL client connected to the
--         'zomerkamp' database.
-- WARNING: ALL DATA WILL BE LOST.
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS change_logs;
DROP TABLE IF EXISTS unavailabilities;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS availability;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS participants;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------
-- participants
-- ----------------------------------------------------------
CREATE TABLE participants (
    id             INT          NOT NULL AUTO_INCREMENT,
    name           VARCHAR(150) NOT NULL,
    email          VARCHAR(254) NOT NULL,
    phone          VARCHAR(50)  NULL,
    remarks        TEXT         NULL,
    submitted_at   VARCHAR(40)  NULL,
    child_first    VARCHAR(100) NULL,
    child_last     VARCHAR(100) NULL,
    child_att_d1   TEXT         NULL,
    child_att_d2   TEXT         NULL,
    child_att_d3   TEXT         NULL,
    child_att_d4   TEXT         NULL,
    child_diet     TEXT         NULL,
    child_notes    TEXT         NULL,
    first_ntc      TINYINT(1)   NOT NULL DEFAULT 0,
    sleep_notes    TEXT         NULL,
    avail_notes    TEXT         NULL,
    has_car        TINYINT(1)   NOT NULL DEFAULT 0,
    parent_diet    TEXT         NULL,
    survey_chat    VARCHAR(120) NULL,
    day1_0700_0730 TINYINT(1)   NOT NULL DEFAULT 0,
    day1_0730_0900 TINYINT(1)   NOT NULL DEFAULT 0,
    day1_0900_1300 TINYINT(1)   NOT NULL DEFAULT 0,
    day1_1300_1530 TINYINT(1)   NOT NULL DEFAULT 0,
    day1_1530_1800 TINYINT(1)   NOT NULL DEFAULT 0,
    day1_1800_2100 TINYINT(1)   NOT NULL DEFAULT 0,
    day2_0700_0730 TINYINT(1)   NOT NULL DEFAULT 0,
    day2_0730_0900 TINYINT(1)   NOT NULL DEFAULT 0,
    day2_0900_1300 TINYINT(1)   NOT NULL DEFAULT 0,
    day2_1300_1530 TINYINT(1)   NOT NULL DEFAULT 0,
    day2_1530_1800 TINYINT(1)   NOT NULL DEFAULT 0,
    day2_1800_2100 TINYINT(1)   NOT NULL DEFAULT 0,
    day3_0700_0730 TINYINT(1)   NOT NULL DEFAULT 0,
    day3_0730_0900 TINYINT(1)   NOT NULL DEFAULT 0,
    day3_0900_1300 TINYINT(1)   NOT NULL DEFAULT 0,
    day3_1300_1530 TINYINT(1)   NOT NULL DEFAULT 0,
    day3_1530_1800 TINYINT(1)   NOT NULL DEFAULT 0,
    day3_1800_2100 TINYINT(1)   NOT NULL DEFAULT 0,
    day4_0700_0730 TINYINT(1)   NOT NULL DEFAULT 0,
    day4_0730_0900 TINYINT(1)   NOT NULL DEFAULT 0,
    day4_0900_1300 TINYINT(1)   NOT NULL DEFAULT 0,
    day4_1300_1530 TINYINT(1)   NOT NULL DEFAULT 0,
    day4_1530_1800 TINYINT(1)   NOT NULL DEFAULT 0,
    day4_1800_2100 TINYINT(1)   NOT NULL DEFAULT 0,
    messaging      ENUM('whatsapp','signal','telegram','sms','none')
                   NOT NULL DEFAULT 'whatsapp',
    `group`        VARCHAR(100) NULL DEFAULT NULL,
    excluded_all_days TINYINT(1) NOT NULL DEFAULT 0,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_participants_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- tasks
-- ----------------------------------------------------------
CREATE TABLE tasks (
    id              INT          NOT NULL AUTO_INCREMENT,
    name            VARCHAR(200) NOT NULL,
    day             INT          NOT NULL,
    begin_time      TIME         NOT NULL,
    end_time        TIME         NOT NULL,
    points          INT          NOT NULL DEFAULT 1,
    people_required INT          NOT NULL DEFAULT 1,
    time_block      ENUM('07:00-07:30', '07:30-09:00', '09:00-13:00', '13:00-15:30', '15:30-18:00', '18:00-21:00') NOT NULL,
    task_number     INT          NULL,
    lead_name       VARCHAR(200) NULL,
    description     TEXT         NULL,
    size            VARCHAR(50)  NULL,
    location        VARCHAR(200) NULL,
    task_notes      TEXT         NULL,
    source_task_number INT       NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_task_day_begin_name (day, begin_time, name),
    UNIQUE KEY uq_task_number (task_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- assignments
-- ----------------------------------------------------------
CREATE TABLE assignments (
    id             INT  NOT NULL AUTO_INCREMENT,
    task_id        INT  NOT NULL,
    participant_id INT  NOT NULL,
    role           ENUM('lead','helper','backup') NOT NULL DEFAULT 'helper',
    points_awarded INT  NOT NULL DEFAULT 0,
    confirmed      TINYINT(1) NOT NULL DEFAULT 1,
    notes          TEXT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_task_participant (task_id, participant_id),
    CONSTRAINT fk_asgn_task        FOREIGN KEY (task_id)        REFERENCES tasks(id)        ON DELETE CASCADE,
    CONSTRAINT fk_asgn_participant FOREIGN KEY (participant_id) REFERENCES participants(id)  ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- availability
-- ----------------------------------------------------------
CREATE TABLE availability (
    id             INT  NOT NULL AUTO_INCREMENT,
    participant_id INT  NOT NULL,
    day            INT  NOT NULL,
    time_block     ENUM('07:00-07:30', '07:30-09:00', '09:00-13:00', '13:00-15:30', '15:30-18:00', '18:00-21:00') NOT NULL,
    available      TINYINT(1) NOT NULL DEFAULT 0,
    created_at     DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_participant_day_block (participant_id, day, time_block),
    CONSTRAINT fk_avail_participant FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- unavailabilities
-- ----------------------------------------------------------
CREATE TABLE unavailabilities (
    id             INT  NOT NULL AUTO_INCREMENT,
    participant_id INT  NOT NULL,
    task_id        INT  NULL,
    day            INT  NULL,
    all_days       TINYINT(1) NOT NULL DEFAULT 0,
    reason         TEXT NULL,
    replacements   TEXT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_unavail_participant FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    CONSTRAINT fk_unavail_task        FOREIGN KEY (task_id)        REFERENCES tasks(id)        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- change_logs
-- ----------------------------------------------------------
CREATE TABLE change_logs (
    id             INT  NOT NULL AUTO_INCREMENT,
    message        TEXT NOT NULL,
    category       VARCHAR(40) NOT NULL DEFAULT 'info',
    participant_id INT  NULL,
    task_id        INT  NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_log_participant FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE SET NULL,
    CONSTRAINT fk_log_task        FOREIGN KEY (task_id)        REFERENCES tasks(id)        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
