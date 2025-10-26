# Log in to ECR
# aws ecr create-repository --repository-name incar-assist/intent-classification

AWS_BUCKET=data-daizika-com
AWS_MODEL_PREFIX=incar_assist/model
MODEL_IC=roberta-student-distilled
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REPO=incar-assist
IMAGE_TAG=intent-classification
ECR_URI=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO}/${IMAGE_TAG}:latest

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

rm -rf ./${MODEL_IC}
aws s3 cp s3://${AWS_BUCKET}/${AWS_MODEL_PREFIX}/${MODEL_IC}/ ./${MODEL_IC} --recursive

# Build for linux/amd64 (Lambda’s arch), unless you choose arm64 base image
docker build -t ${REPO}/${IMAGE_TAG} .
docker tag ${REPO}/${IMAGE_TAG}:latest ${ECR_URI}
docker push ${ECR_URI}

