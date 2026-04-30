FROM python:3.9-slim
WORKDIR /app
COPY client.py ./
COPY . /app
RUN pip install psutil
CMD ["python", "client.py"]
