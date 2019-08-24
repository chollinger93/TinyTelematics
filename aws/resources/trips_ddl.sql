CREATE EXTERNAL TABLE IF NOT EXISTS telematics.trips (
  `id` string,
  `lat` double,
  `long` double,
  `altitude` double,
  `ts` string,
  `speed` double
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1',
  'ignore.malformed.json' = 'true',
  "mapping.ts" = "timestamp"
) LOCATION 's3://$BUCKET/2019/'
TBLPROPERTIES ('has_encrypted_data'='false');