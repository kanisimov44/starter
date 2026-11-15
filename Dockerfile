FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY starter.py test_starter.py ./

# По умолчанию запускаются тесты; пример: docker run --rm starter-tests python starter.py
CMD ["python", "-m", "pytest", "-v"]
