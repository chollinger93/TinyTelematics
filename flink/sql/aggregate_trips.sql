CREATE OR REPLACE VIEW telematics.tripLines AS (
SELECT
	tripId,
	ST_AsGeoJSON(
		LineStringFromText(
			CONCAT("LINESTRING(",
				GROUP_CONCAT(
				CONCAT(lon, " ", lat))
				, ")")
		)
	) as tripLine,
	AVG(speed) as averageSpeed,
	COUNT(*) as points,
	MIN(ts) as start_ts,
	MAX(ts) as end_ts
FROM (SELECT * FROM telematics.trips ORDER BY ts ASC) t
GROUP BY
	tripId
)