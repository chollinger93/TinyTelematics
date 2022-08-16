package com.chollinger.telematics

import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.connector.kafka.source.KafkaSource
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer
import org.apache.flink.api.scala._
import io.circe.generic.auto._
import org.apache.flink.connector.kafka.source.reader.deserializer.KafkaRecordDeserializationSchema
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}
import org.apache.kafka.common.serialization.{Deserializer, Serde, Serdes, StringDeserializer}
import org.apache.flink.streaming.api.scala._
import com.chollinger.telematics.model.GpsModel.GpsPoint
import com.chollinger.telematics.model.GpsModel.GpsPoint._
import io.circe
import io.circe.{Decoder, Encoder, jawn}
import org.apache.flink.api.common.typeinfo.TypeInformation
import org.apache.flink.streaming.api.datastream.DataStreamSink
import org.apache.flink.util.Collector
import org.apache.kafka.clients.consumer.{ConsumerRecord, OffsetResetStrategy}

object Job {

  def buildSource[A: Decoder](
      bootstrapServers: String,
      topics: String,
      groupId: String
  )(implicit typeInfo: TypeInformation[A]): KafkaSource[A] = {
    KafkaSource
      .builder[A]
      .setBootstrapServers(bootstrapServers)
      .setTopics(topics)
      .setGroupId(groupId)
      // Start from committed offset, also use EARLIEST as reset strategy if committed offset doesn't exist
      .setStartingOffsets(
        OffsetsInitializer.committedOffsets(OffsetResetStrategy.EARLIEST)
      )
      .setDeserializer(
        new KafkaRecordDeserializationSchema[A] {
          override def deserialize(
              record: ConsumerRecord[Array[Byte], Array[Byte]],
              out: Collector[A]
          ): Unit = {
            val s                         = new StringDeserializer().deserialize(topics, record.value())
            val v: Either[circe.Error, A] = jawn.decode[A](s)
            v match {
              case Left(e)      => println(e)
              case Right(value) => out.collect(value)
            }
          }

          override def getProducedType: TypeInformation[A] = typeInfo
        }
      )
      .build
  }

  def main(args: Array[String]): Unit = {
    // Require a streaming environment
    val env                                 = StreamExecutionEnvironment.createLocalEnvironment()
    implicit val encoder: Encoder[GpsPoint] = implicitly
    val data: DataStream[GpsPoint] = env.fromSource(
      buildSource[GpsPoint](
        "192.168.1.213:19092",
        "test",
        "flink-telematics"
      ),
      WatermarkStrategy.noWatermarks(), // TODO: wats
      "Kafka Source"
    )
    // Print for testing
    val p: DataStreamSink[GpsPoint] = data.print()
    // Write to Iceberg

    // execute program
    env.execute("Telematics v3")
  }
}
