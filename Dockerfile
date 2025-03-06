FROM python:3.13.1-alpine3.20 AS builder

RUN python -m venv /py 
COPY ./requirements.txt /tmp/requirements.txt
RUN /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt

FROM builder AS runner

ENV PYHTONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/py/bin:$PATH"

COPY ./src /app

RUN rm -r /tmp
RUN adduser --disabled-password --no-create-home django-user
USER django-user

WORKDIR /app
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "app.wsgi:application"]

