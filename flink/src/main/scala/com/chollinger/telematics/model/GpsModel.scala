package com.chollinger.telematics.model

import derevo.circe.{decoder, encoder}
import derevo.derive
import org.apache.flink.api.common.typeinfo.TypeInformation

object GpsModel {

  type Meters          = Double
  type MetersPerSecond = Meters
  type Latitude        = Meters
  type Longitude       = Meters
  type Altitude        = Meters
  type Speed           = MetersPerSecond
  type EpochMs         = Double

  type ID = String
  @derive(encoder, decoder)
  final case class GpsPoint(
      id: ID,
      lat: Latitude,
      lon: Longitude,
      altitude: Altitude,
      speed: Speed,
      timestamp: EpochMs
  )
  object GpsPoint {
    implicit val typeInfo: TypeInformation[GpsPoint] = TypeInformation.of(classOf[GpsPoint])
  }
}
