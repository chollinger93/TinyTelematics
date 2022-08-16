package com.chollinger.telematics.model

import io.estatico.newtype.macros.newtype

import java.util.{Date, UUID}

object GpsModel {

  sealed trait GpsMeasurement {
    def value: Double
  }
  final case class Latitude(value: Double) extends GpsMeasurement
  final case class Longitude(value: Double) extends GpsMeasurement

  @newtype final case class Altitude(meters: Double)
  @newtype final case class Speed(metersPerSecond: Double)

  final case class GpsPoint(
      id: UUID,
      lat: Latitude,
      lon: Longitude,
      altitude: Altitude,
      speed: Speed,
      timestamp: Date
  )
}
