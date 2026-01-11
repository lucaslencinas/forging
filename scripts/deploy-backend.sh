#!/bin/bash
# Deploy backend to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="us-central1"
SERVICE_NAME="forging-backend"
IMAGE_NAME="gcr.io/$PROJECT_ID/forging-backend"

echo "🔨 Building Docker image..."
cd "$(dirname "$0")/../backend"
docker build -t $IMAGE_NAME .

echo "📤 Pushing to Google Container Registry..."
docker push $IMAGE_NAME

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --set-env-vars "GCS_BUCKET_NAME=forging-uploads"

echo "✅ Backend deployed!"
echo "🔗 Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
