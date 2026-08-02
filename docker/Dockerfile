FROM python:3.12-slim

WORKDIR /app

COPY application/server/web/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY application/__init__.py ./application/__init__.py
COPY application/server/__init__.py ./application/server/__init__.py
COPY application/server/web ./application/server/web

ENV PYTHONUNBUFFERED=1

# Cloud Run sets $PORT and expects the container to listen on it (0.0.0.0),
# not a fixed port -- 8080 is only the local-run fallback.
CMD exec uvicorn application.server.web.app:app --host 0.0.0.0 --port ${PORT:-8080}
