# Tiny Telematics
A telematics showcase for my blog.
 
## The Hadoop Way
The original article used Spark, Hive, and Zeppelin to process the data and can be found [here](https://chollinger.com/blog/2017/03/tiny-telematics-with-spark-and-zeppelin/).

![Hadoop Architecture](./docs/hadoop-arch.png)

![Zeppelin](./docs/zeppelin.jpg)

## The AWS Way
The "new" way is using AWS with IoT Greengrass, Kinesis Firehose, Lambda, Athena, and QuickSight and can be found [here](https://chollinger.com/blog/2019/08/how-i-built-a-tiny-real-time-telematics-application-on-aws/).

It depends on a physical GPS dongle, as it uses the `gps` Kernel module.


![AWS Architecture](./docs/aws-arch.png)

![AWS Architecture](./docs/aws-visual.png)

# AWS Setup
Please see the blog article for AWS details.

For the local setup, a Linux kernel is required.

## Lambda
Please see `lambda/telematics-input/deploy_venv.sh` for the deployment script.

## GPSD
Please see `sbin/setup_gps.sh` for the GPS setup. Mileage will vary depending on your distribution.

# Hadoop Setup
You will need Hive, Spark, Zeppelin, HDFS, Yarn, and Zookeeper.

## Compile Spark
```
cd spark
sbt build
sbt package
spark-submit --files hive-site.xml --jars mysql-connector-java-5.1.40-bin.jar ./target/scala-2.10/TinyTelematics_2.10-1.0.jar
```

## Zeppelin
Import `zepppelin/telematics.json`

