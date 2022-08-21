FROM python:3.8-bullseye

VOLUME /config

COPY sbin/ .
COPY sbin/init.sh .
COPY tiny_telematics/ ./tiny_telematics/
COPY pyproject.toml .

# Deps
RUN ./setup_gps.sh
# For crypography/poetry, we need the Rust compiler for ARM
RUN apt-get update 
RUN apt-get install build-essential libssl-dev libffi-dev python3-dev cargo -y
RUN pip install --upgrade pip
RUN pip install -v cryptography==37.0.4
RUN pip install -v poetry==1.1.14
# Build
RUN poetry build
RUN pip install --force-reinstall dist/tiny_telematics-0.1.0-py3-none-any.whl

# Start
ENTRYPOINT ["/bin/bash", "init.sh"]