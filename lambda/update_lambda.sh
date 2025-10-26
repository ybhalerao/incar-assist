#! /bin/bash

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REPO=incar-assist
IMAGE_TAG=intent-classification
ECR_URI=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO}/${IMAGE_TAG}:latest

aws lambda update-function-code \
  --region us-east-1 \
  --function-name incar_assist_ic \
  --image-uri ${ECR_URI} \
  --publish

IMAGE_TAG=tod
ECR_URI=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO}/${IMAGE_TAG}:latest

aws lambda update-function-code \
  --region us-east-1 \
  --function-name incar_assist_tod \
  --image-uri ${ECR_URI} \
  --publish

