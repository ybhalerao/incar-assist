#! /bin/bash

aws lambda update-function-code \
  --region us-east-1 \
  --function-name incar_assist_ic \
  --s3-bucket data-daizika-com \
  --s3-key incar_assist/lambda/incar_assist_ic.zip
