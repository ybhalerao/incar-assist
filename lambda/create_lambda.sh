#! /bin/bash

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REPO=incar-assist

IMAGE_TAG=intent-classification
ECR_URI=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO}/${IMAGE_TAG}:latest

aws lambda create-function \
--region ${REGION} \
--function-name incar_assist_ic  \
--package-type Image \
--code ImageUri=${ECR_URI} \
--role arn:aws:iam::922595822895:role/lambda-vpc-execution-role \
--timeout 30 \
--memory-size 1024 \
--ephemeral-storage '{"Size": 2048}' \

IMAGE_TAG=tod
ECR_URI=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO}/${IMAGE_TAG}:latest

aws lambda create-function \
--region ${REGION} \
--function-name incar_assist_tod  \
--package-type Image \
--code ImageUri=${ECR_URI} \
--role arn:aws:iam::922595822895:role/lambda-vpc-execution-role \
--timeout 30 \
--memory-size 1024 \
--ephemeral-storage '{"Size": 2048}' \

  