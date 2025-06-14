# Use official Python image
FROM python:3.9

# Set the working directory
WORKDIR /code

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose Flask port
EXPOSE 5050

# Run Flask
CMD ["python3", "app/main.py"]

