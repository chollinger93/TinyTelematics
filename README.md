# Tiny Telematics
A telematics showcase for my blog.

The project collects data from a driver and generates reports and dashboards.

The project is split into 2 logical elements: `Hadoop` and `AWS`. The below sections explain the differences.

The `Hadoop` way uses batch processing and relies on [SensorLog](https://apps.apple.com/us/app/sensorlog/id388014573), an iOS app. Other than that, it is entirely based on Open Source.

The `AWS` way is vendor-locked to AWS (to a degree), but processes data in real-time. It relies on a physical GPS dongle.
 
## The Hadoop Way
The original article used Spark, Hive, and Zeppelin to process the data and can be found [here](https://chollinger.com/blog/2017/03/tiny-telematics-with-spark-and-zeppelin/).

![Hadoop Architecture](./docs/hadoop-arch.png)

![Zeppelin](./docs/zeppelin.jpg)

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

## License
This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE) file for details.
