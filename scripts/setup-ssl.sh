#!/bin/bash

# Install certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Stop nginx temporarily
sudo docker-compose down

# Get SSL certificate
sudo certbot certonly --standalone \
  -d api.yoon.today \
  --email yoonju977@gmail.com \
  --agree-tos \
  --non-interactive

# Copy certificates to nginx ssl directory
sudo mkdir -p ./nginx/ssl
sudo cp /etc/letsencrypt/live/api.yoon.today/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/api.yoon.today/privkey.pem ./nginx/ssl/

# Set proper permissions
sudo chown -R $USER:$USER ./nginx/ssl/
sudo chmod -R 600 ./nginx/ssl/

# Start services
sudo docker-compose up -d 