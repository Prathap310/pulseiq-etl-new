FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Src/ ./Src/
COPY 03_Data/csv/ ./03_Data/csv/
COPY Data/ ./Data/
COPY Logs/ ./Logs/
COPY Docs/ ./Docs/

RUN mkdir -p Data/Clean Data/Rejected Logs

CMD ["python", "Src/run_pipeline.py"]
