CREATE DATABASE telematics;

CREATE TABLE telematics.trips (
	`id` BIGINT NOT NULL AUTO_INCREMENT,
	`userId` BIGINT NOT NULL,
	`lat` DOUBLE,
	`lon` DOUBLE,
	`altitude` DOUBLE,
	`speed` DOUBLE,
	`ts` TIMESTAMP NOT NULL,
	`updated_at` TIMESTAMP NOT NULL,
	PRIMARY KEY(id, userId)
);