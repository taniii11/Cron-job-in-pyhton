-- Create the database (without IF NOT EXISTS)
CREATE DATABASE `admiral_db`;
USE `admiral_db`;

-- Create router_list_tb
CREATE TABLE `router_list_tb` (
  `router_list_id` INT(11) NOT NULL AUTO_INCREMENT,
  `router_id` INT(11) NOT NULL,
  `name` VARCHAR(75) NOT NULL,
  `user_group` VARCHAR(20) NOT NULL,
  `group_id` VARCHAR(20) DEFAULT NULL,
  `latitude` VARCHAR(20) NOT NULL,
  `longitude` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`router_list_id`),
  KEY `router_id` (`router_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Create router_health_tb
CREATE TABLE `router_health_tb` (
  `router_health_id` INT(11) NOT NULL AUTO_INCREMENT,
  `router_id` INT(11) NOT NULL,
  `interface` VARCHAR(10) NOT NULL,
  `date` DATETIME DEFAULT NULL,
  `download` INT(25) NOT NULL,
  `upload` INT(25) NOT NULL,
  `cpu_usage` INT(25) NOT NULL,
  `ram_usage` INT(25) NOT NULL,
  `disk_usage` INT(25) NOT NULL,
  PRIMARY KEY (`router_health_id`),
  KEY `router_id` (`router_id`),
  CONSTRAINT `router_health_tb_ibfk_1`
    FOREIGN KEY (`router_id`) REFERENCES `router_list_tb` (`router_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Create speed_test_tb
CREATE TABLE `speed_test_tb` (
  `speed_test_id` INT(11) NOT NULL AUTO_INCREMENT,
  `router_id` INT(11) NOT NULL,
  `date` DATETIME DEFAULT NULL,
  `id` INT(11) NOT NULL,
  `download_speed_mbps` VARCHAR(25) NOT NULL,
  `upload_speed_mbps` VARCHAR(25) NOT NULL,
  `latency1_ms` INT(11) NOT NULL,
  `latency2_ms` INT(11) DEFAULT NULL,
  `latency3_ms` INT(11) DEFAULT NULL,
  `protocol` VARCHAR(25) DEFAULT NULL,
  `company_id` VARCHAR(20) NOT NULL,
  `management_name` VARCHAR(20) DEFAULT NULL,
  PRIMARY KEY (`speed_test_id`),
  KEY `router_id` (`router_id`),
  CONSTRAINT `speed_test_tb_ibfk_1`
    FOREIGN KEY (`router_id`) REFERENCES `router_list_tb` (`router_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
