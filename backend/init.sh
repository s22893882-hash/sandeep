#!/bin/bash
# Backend initialization script
# This script runs on container startup

set -e

echo "Initializing backend..."

# Create necessary directories
mkdir -p /app/logs
mkdir -p /app/data

# Set permissions
chown -R appuser:appuser /app/logs
chown -R appuser:appuser /app/data

# Wait for dependencies
echo "Waiting for MongoDB..."
until python -c "import pymongo; client = pymongo.MongoClient('mongodb://admin:password123@mongodb:27017', serverSelectionTimeoutMS=5000)"; do
    echo "MongoDB not ready, waiting..."
    sleep 2
done
echo "MongoDB is ready!"

echo "Waiting for Redis..."
until python -c "import redis; r = redis.Redis(host='redis', port=6379, socket_timeout=5)"; do
    echo "Redis not ready, waiting..."
    sleep 2
done
echo "Redis is ready!"

echo "Backend initialization complete!"
echo "Starting application..."

# Execute the main command
exec "$@"
