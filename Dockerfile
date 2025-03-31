ARG BUILD_ENV=production

FROM python:3.13.1-alpine3.20 AS base_image

FROM base_image AS development_builder

ONBUILD COPY ./.certs/netskope-cert-bundle.pem /etc/ssl/certs/netskope-cert-bundle.pem
ONBUILD ENV SSL_CERT_FILE=/etc/ssl/certs/netskope-cert-bundle.pem
ONBUILD ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/netskope-cert-bundle.pem
ONBUILD ENV CURL_CA_BUNDLE=/etc/ssl/certs/netskope-cert-bundle.pem

FROM base_image AS production_builder

FROM ${BUILD_ENV}_builder as builder

RUN apk add --update --no-cache \
    postgresql-client &&\
    apk add --update --no-cache --virtual .tmp-build-deps \
    build-base \
    postgresql-dev \
    musl-dev
RUN python -m venv /py
COPY ./requirements.txt /tmp/requirements.txt
RUN /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt

RUN rm -r /tmp &&\
    apk del .tmp-build-deps

FROM builder AS runner

ENV PYHTONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/py/bin:$PATH"

COPY ./src /app


RUN adduser --disabled-password --no-create-home django-user
USER django-user

WORKDIR /app
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "app.wsgi:application"]

