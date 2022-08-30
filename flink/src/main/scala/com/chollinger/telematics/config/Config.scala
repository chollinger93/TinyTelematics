package com.chollinger.telematics.config

import pureconfig.ConfigSource
import pureconfig.error.ConfigReaderFailures
import pureconfig.generic.auto.exportReader

object Config {
  final case class Config(kafka: KafkaConfig, jdbc: JdbcConfig)
  final case class KafkaConfig(bootstrapServers: String, topics: String, groupId: String)
  final case class JdbcConfig(url: String, driverName: String, user: String, password: String)

  sealed trait Environment
  case object Local      extends Environment
  case object Production extends Environment
  def loadConfig(): Either[ConfigReaderFailures, Config] = sys.env.get("RUN_LOCALLY") match {
    case Some(_) => ConfigSource.default.load[Config]
    case _       => ConfigSource.resources("production.conf").load[Config]
  }

}
