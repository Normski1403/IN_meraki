# Use a lightweight Python base image
FROM python:3.12-slim

# Set a working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Set the entrypoint for the application
CMD ["python", "new_script.py"]
