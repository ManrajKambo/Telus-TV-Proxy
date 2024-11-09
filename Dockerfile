FROM python:3.13-slim-bullseye

WORKDIR /app

RUN pip install Flask requests requests[socks] waitress redis

COPY TelusTV.py .
COPY app.py .

CMD ["python", "-u", "app.py"]