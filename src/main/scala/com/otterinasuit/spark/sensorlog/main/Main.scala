package com.otterinasuit.spark.sensorlog.main

import org.apache.spark.api.java.JavaRDD
import org.apache.spark.sql.{Row, SaveMode, SparkSession, functions}
import org.apache.spark.sql.types._
import org.apache.spark.sql.functions

/*
 * Tiny telematics Spark code
 * @author otter-in-a-suit
 */

object Main {

  def main(args: Array[String]): Unit = {
    // Create a Scala Spark Context.
    val sc = SparkSession
      .builder()
      .appName("TinyTelematics")
      .master("local[2]")
      .config("spark.sql.warehouse.dir", "file:///tmp/spark-warehouse")
      .enableHiveSupport()
      .getOrCreate()

     /*
     * Build the schema & load the raw data
     */

    // Build the schema
    // I honestly don't know how to dynamically infer the schema by type - the old spark-csv library from databricks was able to do that as far as I recall...
    val schemaStringMeta = "loggingTime loggingSample identifierForVendor deviceID locationTimestamp_since1970"
    val schemaStringData = "locationLatitude locationLongitude locationAltitude locationSpeed locationCourse locationVerticalAccuracy locationHorizontalAccuracy locationHeadingTimestamp_since1970 locationHeadingX locationHeadingY locationHeadingZ locationTrueHeading locationMagneticHeading locationHeadingAccuracy accelerometerTimestamp_sinceReboot accelerometerAccelerationX accelerometerAccelerationY accelerometerAccelerationZ gyroTimestamp_sinceReboot gyroRotationX gyroRotationY gyroRotationZ motionTimestamp_sinceReboot motionYaw motionRoll motionPitch motionRotationRateX motionRotationRateY motionRotationRateZ motionUserAccelerationX motionUserAccelerationY motionUserAccelerationZ"
    val schemaStringActivityStrings = "motionAttitudeReferenceFrame motionQuaternionX motionQuaternionY motionQuaternionZ motionQuaternionW motionGravityX motionGravityY motionGravityZ motionMagneticFieldX motionMagneticFieldY motionMagneticFieldZ motionMagneticFieldCalibrationAccuracy " +
      "activityTimestamp_sinceReboot activity activityActivityConfidence activityActivityStartDate pedometerStartDate pedometerNumberofSteps pedometerDistance pedometerFloorAscended pedometerFloorDescended pedometerEndDate altimeterTimestamp_sinceReboot altimeterReset altimeterRelativeAltitude altimeterPressure IP_en0 IP_pdp_ip0 deviceOrientation batteryState batteryLevel state"

    // String
    val fieldsMeta = schemaStringMeta.split(" ")
      .map(fieldName => StructField(fieldName, StringType, nullable = true))

    // Double
    val fieldsData = schemaStringData.split(" ")
      .map(fieldName => StructField(fieldName, DoubleType, nullable = true))

    // String
    val fieldsActivity = schemaStringActivityStrings.split(" ")
      .map(fieldName => StructField(fieldName, StringType, nullable = true))
    val schema = StructType(fieldsMeta ++ fieldsData ++ fieldsActivity)

    // Read the input files
    // Assumes the input files does not have a header line - filter that here, in your ETL pipeline or with magic
    // We drop duplicates based on the TS - if y'all need more data points, drop that line and adjust the windowing magic
    val input = sc.read.format("csv").schema(schema)
      .load("/Users/christian/Documents/SensorLog/tiny/*.csv")
      .filter(col => !col.get(0).equals("loggingTime"))
      .dropDuplicates("locationTimestamp_since1970")

    /*
     * Spark Windowing function, introduced in Spark 1.4
     * Basic idea: Split the dataframe when the timestamp difference is >= minTripLengthInS
     */
    input.createOrReplaceTempView("input")
    var cols = "loggingSample, identifierForVendor, deviceID, locationTimestamp_since1970, locationLatitude, locationLongitude, locationAltitude, locationSpeed, locationCourse"
    // The number of rows to lag can optionally be specified. If the number of rows to lag is not specified, the lag is one row.
    val lag = 1
    val splitBy = "locationTimestamp_since1970"

    // Add a column that includes the next row in a window, i.e. the next timestamp
    val dfDiffRaw = sc.sql("SELECT "+cols+", " +
      "(lag("+splitBy+", "+lag+") " +
      "OVER (PARTITION BY identifierForVendor ORDER BY "+splitBy+" ASC)) AS ts1 " +
      "FROM input")
    // Calculate the timestamp difference to the previous data point
    // Convert EPOCH to normal format for Hive partionining
    val dfDiff = dfDiffRaw.filter(dfDiffRaw.col("ts1").isNotNull)
      .withColumn("diff", dfDiffRaw.col("locationTimestamp_since1970")-dfDiffRaw.col("ts1"))
      .withColumn("year", org.apache.spark.sql.functions.from_unixtime(dfDiffRaw.col("locationTimestamp_since1970")).substr(0,4))
      .withColumn("month", org.apache.spark.sql.functions.from_unixtime(dfDiffRaw.col("locationTimestamp_since1970")).substr(6,2))
    dfDiff.show(40)

    // Cluster the data based on a minimum idle time between data points
    // If you did not collect data for x seconds, start a new "trip"
    val minTripLengthInS = 60
    val tripBy = "diff"
    cols = cols + ", year, month"
    dfDiff.createOrReplaceTempView("diffInput")
    val fullTrips = sc.sql("select "+cols+", diff, segment, " +
      " sum(case when "+tripBy+" > "+minTripLengthInS+" then locationTimestamp_since1970 else 0 end) " +
      " over (partition by identifierForVendor order by "+splitBy+") as trip" +
      " from (select "+cols+",diff," +
      "             lag("+tripBy+", "+lag+") " +
      "             over (partition by identifierForVendor order by "+tripBy+" asc) as segment" +
      "      from diffInput" +
      "     ) ue")

    /*
     * Calculate KPIs
     * We stick to m/s - freedom must follow later, as it is more precise than MPH
     */
     // Group by trip
    val trips = fullTrips.groupBy("trip")

    // Calculate KPIs
    val avgSpeeds = trips.avg("locationSpeed").withColumnRenamed("avg(locationSpeed)", "avgSpeed")
    val topSpeeds = trips.max("locationSpeed").withColumnRenamed("max(locationSpeed)", "topSpeed")

    val result = fullTrips.join(avgSpeeds, "trip").join(topSpeeds, "trip")
    result.show(50)
    // Save
    result.createOrReplaceTempView("result")

    result.write.format("parquet").mode(SaveMode.Append).saveAsTable("telematics")
  }

  /*
 * mnemonic to the array index
 * i.e. header(row,"col") -> col(x)
 */
  @Deprecated
  class SimpleCSVHeader(header: Array[String]) extends Serializable {
    val index = header.zipWithIndex.toMap

    def apply(array: Array[String], key: String): String = array(index(key))
  }
}
