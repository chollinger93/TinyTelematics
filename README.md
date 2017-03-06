# Tiny telematics
A telematics showcase for my blog article, available on https://otter-in-a-suit.com/blog/?p=85

## Compile and run
sbt build
sbt package
spark-submit --files hive-site.xml --jars mysql-connector-java-5.1.40-bin.jar ./target/scala-2.10/TinyTelematics_2.10-1.0.jar

## Zeppelin
Import zepppelin/telematics.json

## Todo
- Enable properties
- Use different SensorLog values
- Enable SparkStreaming