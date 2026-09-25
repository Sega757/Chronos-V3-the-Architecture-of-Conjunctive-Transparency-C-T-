FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Compile protos
RUN python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/*.proto

EXPOSE 50051

CMD ["python", "chronos_nexus.py", "--port", "50051"]
