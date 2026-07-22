#!/usr/bin/env bash
# Build the shared arm64 Lambda image, push it to ECR, and deploy the stack.
# Prereqs: aws configured, docker running, and the OpenAI key in SSM:
#   aws ssm put-parameter --name /ticketpilot/openai-api-key --type String \
#       --value "<key>" --overwrite
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
STACK="ticketpilot"
REPO="ticketpilot"
TAG="$(date +%Y%m%d%H%M%S)"        # unique tag so Lambda always pulls the new image
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_URI="${REGISTRY}/${REPO}:${TAG}"

echo ">> ensuring ECR repo ${REPO}"
aws ecr describe-repositories --repository-names "$REPO" --region "$REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$REPO" --region "$REGION" >/dev/null

echo ">> docker login to ECR"
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

echo ">> build + push ${IMAGE_URI}"
docker build --platform linux/arm64 -t "$IMAGE_URI" -f "$ROOT/infra/Dockerfile" "$ROOT"
docker push "$IMAGE_URI"

echo ">> deploy stack ${STACK}"
aws cloudformation deploy \
  --template-file "$ROOT/infra/template.yaml" \
  --stack-name "$STACK" \
  --parameter-overrides ImageUri="$IMAGE_URI" \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --region "$REGION"

echo ">> outputs"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs" --output table
