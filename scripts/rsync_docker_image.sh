#!/bin/bash
set -euo pipefail

# Usage: ./rsync_docker_image.sh <EC2_PUBLIC_IP> [DOCKER_IMAGE_NAME]
# Example: ./rsync_docker_image.sh 54.123.45.67
#          ./rsync_docker_image.sh 54.123.45.67 custom-image:tag

EC2_IP="$1"
IMAGE_NAME="${2:-wiki-rag-tiny}"
KEY_PATH="/Users/roy/.aws/roy-macbook-2025.pem"
SSH_USER="ec2-user"
TAR_NAME="image.tar"

echo "Saving Docker image '$IMAGE_NAME' to $TAR_NAME..."
docker save -o "$TAR_NAME" "$IMAGE_NAME"

echo "Transferring image to $EC2_IP..."
rsync -avz -e "ssh -i $KEY_PATH" "$TAR_NAME" "$SSH_USER@$EC2_IP:/home/$SSH_USER/"

echo "Loading image on remote host..."
ssh -i "$KEY_PATH" "$SSH_USER@$EC2_IP" "docker load -i /home/$SSH_USER/$TAR_NAME"

echo "Done."

