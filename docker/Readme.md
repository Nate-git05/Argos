# Deploying the web API (Cloud Run)

This builds and runs `application/server/web/app.py` -- the registration API
backing the landing page's Register button. It's a separate deployment from
the daemon (which runs on-robot, see `install/`) and separate from the
frontend (which deploys on Vercel).

**Currently deployed:** project `argos-web-api`, region `europe-west1`,
service URL `https://argos-web-api-55563330003.europe-west1.run.app`.

## Build and deploy

`gcloud builds submit --tag ... -f docker/Dockerfile` no longer works on
current gcloud CLI versions -- `-f` was dropped from the `--tag` path. Use
`docker/cloudbuild.yaml` with `--config` instead:

```
gcloud builds submit --config=docker/cloudbuild.yaml --substitutions=_IMAGE=gcr.io/PROJECT_ID/argos-web-api .
```

The build context (the trailing `.`) has to be the repo root, not `docker/`
-- the Dockerfile copies paths like `application/server/web`, which only
resolve from there.

Store `POSTGRES_URI` in Secret Manager rather than passing it as a plain
env var -- it's a live database credential:

```
printf '%s' 'postgresql+asyncpg://...' | gcloud secrets create postgres-uri --data-file=- --replication-policy=automatic

gcloud secrets add-iam-policy-binding postgres-uri \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

The IAM binding step is required -- Cloud Run's default runtime service
account has no Secret Manager access until granted `secretAccessor` on the
secret. `gcloud run deploy` fails with a clear "Permission denied on
secret" error if it's missing.

```
gcloud run deploy argos-web-api \
  --image gcr.io/PROJECT_ID/argos-web-api \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-secrets POSTGRES_URI=postgres-uri:latest \
  --set-env-vars "^@^ALLOWED_ORIGINS=http://localhost:3000,https://www.xn--args-ira.com"
```

The `"^@^..."` prefix is gcloud's syntax for a custom key/value delimiter --
`ALLOWED_ORIGINS`'s value contains commas, which `--set-env-vars` otherwise
parses as separators between multiple vars. `@` just has to be a character
that doesn't appear in the value itself (the default delimiter is `,`, and
`:` collides with `http://`).

Replace `PROJECT_ID`, `PROJECT_NUMBER`, and `REGION` with your actual
values.

## Required environment variables

- `POSTGRES_URI` -- same connection string used locally, `+asyncpg` driver
  included. Set via Secret Manager (see above), never baked into the image
  or passed as a plain `--set-env-vars` value.
- `ALLOWED_ORIGINS` -- comma-separated list of origins allowed to call this
  API from a browser (CORS). Defaults to `http://localhost:3000,https://www.xn--args-ira.com`
  if unset, but set it explicitly in production.

## After deploying

Cloud Run gives you a service URL (`https://argos-web-api-xxxxx.a.run.app` or
your own mapped domain). Set that as `NEXT_PUBLIC_API_URL` in the web app's
Vercel project settings (both Production and Preview) so the registration
modal points at it instead of its `http://localhost:8001` dev default.
`NEXT_PUBLIC_*` vars are inlined at build time, not read at runtime -- a new
deployment is needed before the change takes effect.
