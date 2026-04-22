FROM python:3.10-slim

WORKDIR /app

# Copy dependency files first for layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn python-multipart pydantic PyPDF2

# Copy the rest of the application
COPY . .

# Expose port for FastAPI
EXPOSE 8080

# Run FastAPI using uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
