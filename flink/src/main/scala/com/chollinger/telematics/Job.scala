package com.chollinger.telematics

import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.connector.kafka.source.KafkaSource
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer
import org.apache.flink.api.scala._
import org.apache.flink.connector.kafka.source.reader.deserializer.KafkaRecordDeserializationSchema
import org.apache.flink.streaming.api.scala.{
  DataStream,
  StreamExecutionEnvironment
}
import org.apache.kafka.common.serialization.{Deserializer, StringDeserializer}
import com.chollinger.telematics.model.GpsModel
import org.apache.kafka.clients.consumer.OffsetResetStrategy

object Job {

  type BootstrapServer = String
  def buildSource[A](
      bootstrapServers: String,
      topics: String,
      groupId: String
  )(implicit
      serializer: Deserializer[A]
  ): KafkaSource[A] = {
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
        KafkaRecordDeserializationSchema.valueOnly(serializer.getClass)
      )
      .build
  }

  def main(args: Array[String]): Unit = {
    // Require a streaming environment
    val env = StreamExecutionEnvironment.createLocalEnvironment()
    implicit val serde: Deserializer[String] = new StringDeserializer()
    val data: DataStream[String] = env.fromSource(
      buildSource[String](
        "192.168.1.213:19092",
        "test",
        "flink-telematics"
      ),
      WatermarkStrategy.noWatermarks(), // TODO: wats
      "Kafka Source"
    )
    data.print()
    // execute program
    env.execute("Telematics v3")
  }
}
