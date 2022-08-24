from dataclasses import dataclass


@dataclass
class GeneralConfig:
    expected_wifi_network: str
    shutdown_timer_s: int = 10
    cache_buffer: int = 10
    filter_empty_records: bool = False


@dataclass
class CacheConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0


@dataclass
class KafkaConfig:
    boostrap_servers: str
    topic: str


@dataclass
class Config:
    general: GeneralConfig
    cache: CacheConfig
    kafka: KafkaConfig