ARG BUILD_ENV=production

FROM python:3.13.1-alpine3.20 AS base_builder

RUN python -m venv /py 
COPY ./requirements.txt /tmp/requirements.txt
RUN /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt

FROM base_builder AS dev_builder

COPY ./requirements.dev.txt /tmp/requirements.dev.txt
RUN /py/bin/pip install -r /tmp/requirements.dev.txt

FROM base_builder AS production_builder

FROM ${BUILD_ENV}_builder AS runner

ENV PYHTONUNBUFFERED 1
ENV PATH="/py/bin:$PATH"

COPY ./src /app

RUN rm -r /tmp
RUN adduser --disabled-password --no-create-home django-user
USER django-user

WORKDIR /app
EXPOSE 8000
