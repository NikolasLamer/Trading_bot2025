FROM python:3.11-slim

WORKDIR /app
COPY ./app /app/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

EXPOSE 80
CMD ["python", "-m", "app.main"]
