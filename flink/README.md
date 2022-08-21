
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
export RUN_LOCALLY=1
 JDBC_USER=telematics JDBC_PW=$PASSWORD sbt run
```
## Submit
Create a `src/main/resources/production.conf` first.

```bash
sbt clean assembly
flink run \
      --detached \
      --jobmanager bigiron.lan:8082 \
      ./target/scala-2.12/TinyTelematics-assembly-0.1.jar
```