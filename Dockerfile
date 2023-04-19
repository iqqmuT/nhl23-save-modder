FROM python:3.8-alpine

WORKDIR /code

RUN apk add --no-cache gcc musl-dev
RUN pip install --no-cache-dir lz4==4.3.2

CMD ["python3", "./extract.py"]
