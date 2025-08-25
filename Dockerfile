FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY requirements.txt ./tmp/requirements.txt
COPY . .

RUN pip install -r ./tmp/requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]