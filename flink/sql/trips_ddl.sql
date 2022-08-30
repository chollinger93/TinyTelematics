CREATE TABLE telematics.trips (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
	`tripId` BIGINT NOT NULL,
	`userId` BIGINT NOT NULL,
	`lat` DECIMAL(11,8),
	`lon` DECIMAL(11,8),
	`altitude` DOUBLE,
	`speed` DOUBLE,
	`ts` TIMESTAMP NOT NULL,
	`updated_at` TIMESTAMP NOT NULL,
	PRIMARY KEY(id)
);