FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir zabbix-utils pandas scikit-learn

COPY src/script_aiops.py .

CMD ["python", "script_aiops.py"]
