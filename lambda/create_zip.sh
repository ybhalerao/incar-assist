#! /bin/bash

cd /development/incar-assist/lambda

rm ./*.zip

rm -rf packages
mkdir packages
cd packages

#pip install transformers -t .
pip install torch -t .
#pip install boto3 -t .
#pip install safetensors -t .

zip -r9 ../incar_assist_ic.zip *

cd ../
zip -g incar_assist_ic.zip aws_config.py
zip -g incar_assist_ic.zip incar_assist_ic.py

chmod 666 *.zip

aws s3 cp incar_assist_ic.zip s3://data-daizika-com/incar_assist/lambda/incar_assist_ic.zip
