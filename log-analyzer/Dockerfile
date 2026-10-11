FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY analyzer.py .
EXPOSE 8090
CMD ["uvicorn", "analyzer:app", "--host", "0.0.0.0", "--port", "8090"]
