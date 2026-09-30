FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -e ".[dev]"

EXPOSE 8000

ENTRYPOINT ["python", "-m", "trade_ware.cli"]
CMD ["python", "-m", "uvicorn", "trade_ware.main:app", "--host", "0.0.0.0", "--port", "8000"]
