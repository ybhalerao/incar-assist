#! /bin/bash

aws lambda create-function \
--region us-east-1 \
--function-name incar_assist_ic  \
--role arn:aws:iam::922595822895:role/lambda-vpc-execution-role \
--handler incar_assist_ic.handler \
--runtime python3.12 \
--timeout 30 \
--memory-size 1024 \
--ephemeral-storage '{"Size": 2048}' \
--code S3Bucket=data-daizika-com,S3Key=incar_assist/lambda/incar_assist_ic.zip
