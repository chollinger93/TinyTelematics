CREATE DATABASE telematics;

CREATE TABLE telematics.trips (
	`id` INT NOT NULL AUTO_INCREMENT,
	`userId` INT NOT NULL,
	`lat` DOUBLE,
	`lon` DOUBLE,
	`altitude` DOUBLE,
	`speed` DOUBLE,
	`ts` TIMESTAMP NOT NULL,
	`updated_at` TIMESTAMP NOT NULL,
	PRIMARY KEY(id, userId)
);