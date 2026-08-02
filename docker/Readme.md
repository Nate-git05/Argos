# Deploying the web API (Cloud Run)

This builds and runs `application/server/web/app.py` -- the registration API
backing the landing page's Register button. It's a separate deployment from
the daemon (which runs on-robot, see `install/`) and separate from the
frontend (which deploys on Vercel).

## Build and deploy

```
gcloud builds submit --tag gcr.io/PROJECT_ID/argos-web-api -f docker/Dockerfile .
gcloud run deploy argos-web-api \
  --image gcr.io/PROJECT_ID/argos-web-api \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars POSTGRES_URI="postgresql+asyncpg://...",ALLOWED_ORIGINS="https://www.xn--args-ira.com"
```

Replace `PROJECT_ID` and `REGION` with your actual values. The build context
is the repo root (the trailing `.`), not `docker/` -- the Dockerfile copies
paths like `application/server/web`, which only resolve from there.

## Required environment variables

- `POSTGRES_URI` -- same connection string used locally, `+asyncpg` driver
  included. Set this as a Cloud Run env var or Secret Manager secret, never
  baked into the image.
- `ALLOWED_ORIGINS` -- comma-separated list of origins allowed to call this
  API from a browser (CORS). Defaults to `http://localhost:3000,https://www.xn--args-ira.com`
  if unset, but set it explicitly in production.

## After deploying

Cloud Run gives you a service URL (`https://argos-web-api-xxxxx.a.run.app` or
your own mapped domain). Set that as `NEXT_PUBLIC_API_URL` in the web app's
Vercel project settings so the registration modal points at it instead of
its `http://localhost:8001` dev default.
