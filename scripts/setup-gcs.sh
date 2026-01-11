#!/bin/bash
# Set up Google Cloud Storage bucket for Forging

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
BUCKET_NAME="${GCS_BUCKET_NAME:-forging-uploads}"
REGION="us-central1"

echo "🪣 Creating GCS bucket: $BUCKET_NAME"

# Create bucket with uniform access
gcloud storage buckets create "gs://$BUCKET_NAME" \
  --project=$PROJECT_ID \
  --location=$REGION \
  --uniform-bucket-level-access

# Set lifecycle rule to delete files after 1 day (cleanup old uploads)
cat > /tmp/lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 1}
    }
  ]
}
EOF

echo "⏰ Setting lifecycle policy (auto-delete after 1 day)..."
gcloud storage buckets update "gs://$BUCKET_NAME" \
  --lifecycle-file=/tmp/lifecycle.json

# Set CORS for browser uploads
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": ["*"],
    "method": ["GET", "PUT", "POST", "OPTIONS"],
    "responseHeader": ["Content-Type", "Content-Length", "Content-Range"],
    "maxAgeSeconds": 3600
  }
]
EOF

echo "🌐 Setting CORS policy..."
gcloud storage buckets update "gs://$BUCKET_NAME" \
  --cors-file=/tmp/cors.json

rm /tmp/lifecycle.json /tmp/cors.json

echo "✅ GCS bucket configured!"
echo "📦 Bucket URL: gs://$BUCKET_NAME"
