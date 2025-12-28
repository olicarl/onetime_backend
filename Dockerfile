FROM python:3.10-slim

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy requirements
COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install --system -r requirements.txt

COPY . .

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
