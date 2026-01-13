# GCP Setup for Forging

## Project Information

| Property | Value |
|----------|-------|
| **Project Name** | Forging Cloud |
| **Project ID** | `project-48dfd3a0-58cd-43e5-ae7` |
| **Organization** | `lucasdemoreno93-org` (personal) |
| **Region** | `us-central1` |
| **Owner** | `lucasdemoreno93@gmail.com` |

---

## Services Used

| Service | Resource | Purpose |
|---------|----------|---------|
| **Cloud Run** | `forging-backend` | Backend API |
| **Cloud Run** | `forging-frontend` | Next.js frontend |
| **Cloud Storage** | `forging-uploads` bucket | Video and replay file storage |
| **Firestore** | `(default)` database | Analysis records storage |

---

## Service Accounts

### Primary: GitHub Actions Service Account
**Email**: `github-actions@project-48dfd3a0-58cd-43e5-ae7.iam.gserviceaccount.com`

This is the **single service account** used everywhere for consistency.

**Roles**:
- `roles/artifactregistry.admin` - Push Docker images
- `roles/run.admin` - Deploy to Cloud Run
- `roles/iam.serviceAccountUser` - Act as other SAs
- `roles/datastore.user` - Firestore access
- `roles/storage.admin` - GCS access

**Used by**:
- Cloud Run services (production)
- GitHub Actions (via Workload Identity Federation)
- Local development (via impersonation)

### Default Compute Service Account (not used)
**Email**: `268399199868-compute@developer.gserviceaccount.com`

This is auto-created by GCP but we don't use it. All services use `github-actions` SA instead.

---

## Local Development Authentication

For local development, your personal account impersonates the `github-actions` service account.

### Required IAM Setup

Your personal account needs permission to impersonate the service account:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@project-48dfd3a0-58cd-43e5-ae7.iam.gserviceaccount.com \
  --member="user:lucasdemoreno93@gmail.com" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=project-48dfd3a0-58cd-43e5-ae7
```

### Environment Variables

The service account can be overridden via environment variable:

```bash
# Optional - defaults to github-actions SA
export GCP_SERVICE_ACCOUNT="github-actions@project-48dfd3a0-58cd-43e5-ae7.iam.gserviceaccount.com"
```

---

## Firestore Setup

### Database
- **Type**: Firestore Native mode
- **Location**: `us-central1`
- **Database ID**: `(default)`

### Collections
- `analyses` - Stores analysis records

### Indexes

Composite index for listing public analyses:

```bash
gcloud firestore indexes composite create \
  --project=project-48dfd3a0-58cd-43e5-ae7 \
  --collection-group=analyses \
  --field-config field-path=is_public,order=ASCENDING \
  --field-config field-path=created_at,order=DESCENDING
```

---

## GCS Bucket Setup

### Bucket
- **Name**: `forging-uploads`
- **Location**: `US-CENTRAL1`
- **Storage Class**: Standard

### Structure
```
forging-uploads/
├── videos/          # Uploaded gameplay videos
│   └── {uuid}.mp4
├── replays/         # Uploaded replay/demo files
│   └── {uuid}.aoe2record
│   └── {uuid}.dem
└── analyses/        # (Future) Saved analysis artifacts
    └── {analysis_id}/
        ├── video.mp4
        ├── replay.aoe2record
        └── thumbnail.jpg
```

---

## GitHub Actions Setup

Uses Workload Identity Federation (no service account keys).

### Workload Identity Pool
- **Pool**: `github-pool`
- **Provider**: GitHub OIDC

### Allowed Repositories
- `lllencinas/forging`
- `lucaslencinas/forging`

---

## Quick Reference Commands

### Check active account
```bash
gcloud config get-value account
# Should show: lucasdemoreno93@gmail.com
```

### Check project
```bash
gcloud config get-value project
# Should show: project-48dfd3a0-58cd-43e5-ae7
```

### List all IAM bindings
```bash
gcloud projects get-iam-policy project-48dfd3a0-58cd-43e5-ae7 \
  --flatten="bindings[].members" \
  --format="table(bindings.role,bindings.members)"
```

### List service accounts
```bash
gcloud iam service-accounts list --project=project-48dfd3a0-58cd-43e5-ae7
```

### List Firestore indexes
```bash
gcloud firestore indexes composite list --project=project-48dfd3a0-58cd-43e5-ae7
```
