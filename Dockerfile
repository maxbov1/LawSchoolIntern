# Use official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure config directory exists at runtime
RUN mkdir -p /app/config

# Copy the rest of the app
COPY . .

# Expose Flask port
EXPOSE 5050

# Run Flask
CMD ["python", "app/main.py"]

