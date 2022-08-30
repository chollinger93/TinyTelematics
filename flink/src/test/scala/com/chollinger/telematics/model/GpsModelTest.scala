package com.chollinger.telematics.model
import com.chollinger.telematics.model.GpsModel._
import io.circe.{Json, jawn}
import io.circe.syntax.EncoderOps
import org.scalatest.funsuite.AnyFunSuite

import java.util.{Date, UUID}

class GpsModelTest extends AnyFunSuite {
  test("GpsPoint encodes both ways") {
    val p = GpsPoint(
      100L,
      0x4da7f87ee3cdL,
      lat = 10.0,
      lon = -10.0,
      altitude = 0.0,
      speed = 0.0,
      timestamp = 1660690181680L
    )
    val json: Json = p.asJson
    val decoded    = jawn.decode[GpsModel.GpsPoint](json.noSpaces)
    assert(decoded.isRight)
    decoded match {
      case Right(p2) => assert(p2 == p)
      case _         => assert(false)
    }
    assert(
      json.noSpaces == "{\"tripId\":100,\"userId\":85383823942605,\"lat\":10.0,\"lon\":-10.0,\"altitude\":0.0,\"speed\":0.0,\"timestamp\":1660690181680}"
    )
  }
}
