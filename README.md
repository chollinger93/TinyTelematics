# Tiny Telematics

A (tiny) Telematics solution I built over the years in three different iterations (`Hadoop`, `AWS IoT Greengrass`, and completely locally with `redis`, `Kafka`, and `Flink`), for my [blog](https://chollinger.com/blog/).

## Setup

```bash
pyenv install 3.8.13
poetry env use ~/.pyenv/versions/3.8.13/bin/python3
poetry shell
poetry install
```

## Test

```bash
poetry run pytest tests -v  
```

## GPSD

### Setup
Please see `sbin/setup_gps.sh` for the GPS setup. Mileage will vary depending on your distribution.

#### Version Trouble

The `gps` package is only compatible with `Python 3.8`, because `3.9` removed the `encoding` keyword in `JSONDecoder`:

```bash
TypeError: JSONDecoder.__init__() got an unexpected keyword argument 'encoding'
```

#### ipv6 loopback needs to be enabled

Please see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=818332

```bash
sudo sysctl -w net.ipv6.conf.lo.disable_ipv6=0
```

## 

## License

This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE) file for details.
