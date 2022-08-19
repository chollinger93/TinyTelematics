package com.chollinger.telematics

import com.chollinger.telematics.Sources.buildSource
import com.chollinger.telematics.config.Config
import com.chollinger.telematics.model.GpsModel.GpsPoint
import com.chollinger.telematics.model.GpsModel.GpsPoint._
import io.circe.Encoder
import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.connector.jdbc.{JdbcConnectionOptions, JdbcExecutionOptions, JdbcSink}
import org.apache.flink.streaming.api.datastream.DataStreamSink
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}

object Job {

  def main(args: Array[String]): Unit = {
    // Require a streaming environment
    val env = StreamExecutionEnvironment.createLocalEnvironment()
    // Load config
    val config = Config.loadConfig() match {
      case Right(c) => c
      case Left(e)  => throw new Exception(e.prettyPrint())
    }
    // Build source
    implicit val encoder: Encoder[GpsPoint] = implicitly
    val data: DataStream[GpsPoint] = env.fromSource(
      buildSource[GpsPoint](config.kafka),
      WatermarkStrategy.forMonotonousTimestamps(),
      "Kafka Source"
    )
    // Print for testing
    val _: DataStreamSink[GpsPoint] = data.print()
    // Write to JDBC
    data.addSink(Sinks.jdbcSink(config.jdbc))
    // execute program
    env.execute("Telematics v3")
  }
}
