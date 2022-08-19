FROM python:3.8-buster

VOLUME /config

COPY sbin/ .
COPY sbin/init.sh .
COPY tiny_telematics/ ./tiny_telematics/
COPY pyproject.toml .
COPY poetry.lock .

# Deps
RUN ./setup_gps.sh
RUN pip install poetry==1.1.14
# Build
RUN poetry build
RUN pip install --force-reinstall dist/tiny_telematics-0.1.0-py3-none-any.whl

# Start
ENTRYPOINT ["/bin/bash", "init.sh"]