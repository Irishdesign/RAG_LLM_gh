# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY ./models /app/models

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install chromadb[onnx] to support local embedding and avoid downloading models during build
RUN pip install "chromadb[onnx]"


ENV CHROMA_TELEMETRY_ENABLED=false
ENV TRANSFORMERS_CACHE=/app/embedding_model

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["python", "app.py"]