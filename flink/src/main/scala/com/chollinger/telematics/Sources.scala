package com.chollinger.telematics

import com.chollinger.telematics.config.Config.KafkaConfig
import io.circe
import io.circe.{Decoder, jawn}
import org.apache.flink.api.common.typeinfo.TypeInformation
import org.apache.flink.connector.kafka.source.KafkaSource
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer
import org.apache.flink.connector.kafka.source.reader.deserializer.KafkaRecordDeserializationSchema
import org.apache.flink.util.Collector
import org.apache.kafka.clients.consumer.{ConsumerRecord, OffsetResetStrategy}
import org.apache.kafka.common.serialization.StringDeserializer

object Sources {
  def buildSource[A: Decoder](
      config: KafkaConfig
  )(implicit typeInfo: TypeInformation[A]): KafkaSource[A] = {
    KafkaSource
      .builder[A]
      .setBootstrapServers(config.bootstrapServers)
      .setTopics(config.topics)
      .setGroupId(config.groupId)
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
            jawn.decode[A](
              new StringDeserializer().deserialize(config.topics, record.value())
            ) match {
              case Left(e)      => println(e)
              case Right(value) => out.collect(value)
            }
          }

          override def getProducedType: TypeInformation[A] = typeInfo
        }
      )
      .build
  }
}
