## Development / Bare Metal Deploy

If you want to or need to run this on bare metal, you'll need to set up the following for this to work - 

- Client
  - `Python` w/ `poetry`
  - `gpsd`
  - `redis`
- Server
  - MariaDB/mySQL
  - Kafka

### Client (Raspberry Pi)

```bash
# Install poetry
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
# Install an appropriate python version
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

pyenv install 3.8.13
poetry env use ~/.pyenv/versions/3.8.13/bin/python3
poetry shell
poetry install
```

Get `redis` via a package manger or compile from source.

You can then set up a `systemd` service.

Make sure to set `Environment=UBX_DEVICE=G7020-KT` correctly and/or set up a script in `sbin/ubx` for your chipset.

```bash
sudo cp service/tiny-telematics.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable tiny-telematics 
sudo service tiny-telematics start
```

### `gpsd`

Please see [sbin/setup_gps.sh](sbin/setup_gps.sh) for the GPS setup. Mileage will vary depending on your distribution. It's currently pretty bad.

#### Version Trouble

The `gps` package is only compatible with `Python 3.8`, because `3.9` removed the `encoding` keyword in `JSONDecoder`:

```bash
TypeError: JSONDecoder.__init__() got an unexpected keyword argument 'encoding'
```

This is, however, *not* the fault of the maintainers of `gpsd`, see the issue [here](https://gitlab.com/gpsd/gpsd/-/issues/122), since they do not maintain the `pip` project (or any binaries for that matter). If you can, build it from scratch.

#### ipv6 loopback needs to be enabled

Please see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=818332

```bash
sudo sysctl -w net.ipv6.conf.lo.disable_ipv6=0
```
