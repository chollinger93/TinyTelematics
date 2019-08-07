-- Select all records - ETL should have been done before
SELECT lat, long, speed, cast(from_iso8601_timestamp(ts) as timestamp) as ts
FROM telematics.trips
WHERE lat is NOT null
        AND long is NOT null
        AND lat <>0
        AND long <> 0;

-- Top speed by day
SELECT MAX(speed*2.237) as speed_mph, cast(from_iso8601_timestamp(ts) as date) as dt from telematics.trips
WHERE ts is not null and trim(ts) <> ''
GROUP BY cast(from_iso8601_timestamp(ts) as date)