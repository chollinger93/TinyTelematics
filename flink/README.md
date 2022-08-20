
## Requirements
- A `Kafka` cluster
- A `mariaDB` instance

## Setup
### Database
Create user:
```sql
CREATE DATABASE telematics;
CREATE USER 'telematics'@'localhost' IDENTIFIED BY 'XXXX';
GRANT ALL PRIVILEGES ON telematics.* TO 'telematics'@'localhost';
FLUSH PRIVILEGES;
```

Run DDL in [sql/trips_ddl.sql](trips_ddl.sql)`

## Scala
```bash
# SDKMan is cool
sdk install scala 2.12.16
sdk use scala 2.12.16
sdk install sbt
```

## Run
```bash
export BOOTSTRAP_SERVERS="$SERVER:19092"
export TOPICS="topic"
export GROUP_ID="flink-telematics"
export JDBC_URL=jdbc:mariadb://$SERVER:3306/telematics
export JDBC_DRIVER=org.mariadb.jdbc.Driver
export JDBC_USER=telematics
 JDBC_PW=$PASSWORD sbt run
```
