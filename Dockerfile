FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
COPY app.py app.py

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 51234

ENV ND_PORT=51234

CMD ["python", "app.py"]
