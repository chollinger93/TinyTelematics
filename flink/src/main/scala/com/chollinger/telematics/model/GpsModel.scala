package com.chollinger.telematics.model

import derevo.circe.{decoder, encoder}
import derevo.derive
import org.apache.flink.api.common.typeinfo.TypeInformation
import org.apache.flink.connector.jdbc.JdbcStatementBuilder

import java.io.Serializable
import java.sql.{PreparedStatement, Timestamp}
import java.util.Date

object GpsModel {

  type Meters          = Double
  type MetersPerSecond = Meters
  type Latitude        = Meters
  type Longitude       = Meters
  type Altitude        = Meters
  type Speed           = MetersPerSecond
  type EpochMs         = Long
  type ID              = Long

  @derive(encoder, decoder)
  final case class GpsPoint(
      userId: ID,
      lat: Latitude,
      lon: Longitude,
      altitude: Altitude,
      speed: Speed,
      timestamp: EpochMs
  )

  object GpsPoint {
    implicit val typeInfo: TypeInformation[GpsPoint] = TypeInformation.of(classOf[GpsPoint])
    val query: String =
      "insert into trips (userId, lat, lon, altitude, speed, ts, updated_at) values (?, ?, ?, ?, ?, ?, ? )"
    // noinspection ConvertExpressionToSAM
    // Otherwise: Caused by: java.io.NotSerializableException: Non-serializable lambda
    def statement: JdbcStatementBuilder[GpsPoint] = {
      new JdbcStatementBuilder[GpsPoint] {
        override def accept(statement: PreparedStatement, e: GpsPoint): Unit = {
          statement.setLong(1, e.userId)
          statement.setDouble(2, e.lat)
          statement.setDouble(3, e.lon)
          statement.setDouble(4, e.altitude)
          statement.setDouble(5, e.speed)
          statement.setTimestamp(6, new Timestamp(e.timestamp))
          statement.setTimestamp(7, new Timestamp(new Date().getTime))
        }
      }
    }
  }
}
