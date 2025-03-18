#!/bin/bash

# Script to rebuild the frontend with updated configuration

echo "🏗️ Rebuilding frontend..."

# Change to frontend directory
cd "$(dirname "$0")/../frontend" || exit 1

# Run the build
npm run build

echo "✅ Frontend rebuild complete"
echo "Restart the server to apply changes" 