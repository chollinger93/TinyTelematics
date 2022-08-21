CREATE DATABASE telematics;

CREATE TABLE telematics.trips (
	`tripId` BIGINT NOT NULL,
	`userId` BIGINT NOT NULL,
	`lat` DOUBLE,
	`lon` DOUBLE,
	`altitude` DOUBLE,
	`speed` DOUBLE,
	`ts` TIMESTAMP NOT NULL,
	`updated_at` TIMESTAMP NOT NULL,
	PRIMARY KEY(tripId, userId)
);