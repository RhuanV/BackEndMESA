# Uses a lightweight Python image
FROM python:3.12-slim

# Defines the working directory inside the container
WORKDIR /app

# Installs system dependencies required for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copies only the requirements first (optimizes Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies the rest of the code (backend folder and .env)
COPY . .

# Exposes the port used by FastAPI
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]