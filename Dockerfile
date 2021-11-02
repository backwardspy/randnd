FROM python:3 AS build

WORKDIR /build

ADD . .

RUN pip install poetry==1.2.0a2
RUN poetry build

FROM python:3

WORKDIR /app

ARG wheel=proxy-0.0.0-py3-none-any.whl

COPY --from=build /build/dist/$wheel $wheel
COPY --from=build /build/asgi.py asgi.py

RUN pip install $wheel && rm $wheel

CMD ["gunicorn", "asgi:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5500"]
