package com.chollinger.telematics

import com.chollinger.telematics.Sources.buildSource
import com.chollinger.telematics.config.Config
import com.chollinger.telematics.model.GpsModel.GpsPoint
import com.chollinger.telematics.model.GpsModel.GpsPoint._
import io.circe.Encoder
import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.api.common.restartstrategy.RestartStrategies
import org.apache.flink.api.common.time.Time
import org.apache.flink.streaming.api.datastream.DataStreamSink
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}

import java.time.{Duration => JDuration}
import java.util.concurrent.TimeUnit

object Job {

  def main(args: Array[String]): Unit = {
    // Require a streaming environment
    val env = StreamExecutionEnvironment.getExecutionEnvironment
    env.setRestartStrategy(
      RestartStrategies.fixedDelayRestart(
        3,                            // number of restart attempts
        Time.of(10, TimeUnit.SECONDS) // delay
      )
    )
    // Load config
    val config = Config.loadConfig() match {
      case Right(c) => c
      case Left(e)  => throw new Exception(e.prettyPrint())
    }
    // Build source
    implicit val encoder: Encoder[GpsPoint] = implicitly
    val data: DataStream[GpsPoint] = env.fromSource(
      buildSource[GpsPoint](config.kafka),
      WatermarkStrategy.forBoundedOutOfOrderness(JDuration.ofSeconds(10)),
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
