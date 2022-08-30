package com.chollinger.telematics

import com.chollinger.telematics.config.Config.JdbcConfig
import com.chollinger.telematics.model.GpsModel.GpsPoint
import org.apache.flink.connector.jdbc.{JdbcConnectionOptions, JdbcExecutionOptions, JdbcSink}
import org.apache.flink.streaming.api.functions.sink.SinkFunction

import java.sql.PreparedStatement

object Sinks {

  // TODO: exactlyOnceSink
  // TODO: typeclass
  def jdbcSink(config: JdbcConfig): SinkFunction[GpsPoint] = {
    JdbcSink.sink[GpsPoint](
      GpsPoint.query,
      GpsPoint.statement,
      JdbcExecutionOptions
        .builder()
        .withBatchSize(100)
        .withBatchIntervalMs(200)
        .withMaxRetries(5)
        .build(),
      new JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
        .withUrl(config.url)
        .withDriverName(config.driverName)
        .withUsername(config.user)
        .withPassword(config.password)
        .build()
    )
  }
}
