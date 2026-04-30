FROM python:3.9-slim
WORKDIR /app
COPY . /app
COPY server.py ./
RUN pip install psutil
RUN mkdir -p uploads
EXPOSE 1020
CMD ["python", "server.py", "1020"]
