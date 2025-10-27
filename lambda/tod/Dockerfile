# Use AWS Lambda Python 3.10 base
FROM public.ecr.aws/lambda/python:3.13

# Install system deps (strip is handy for size trimming; optional)
#RUN yum -y install binutils && yum clean all

# Copy and install Python deps
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Make the directories
RUN mkdir ${LAMBDA_TASK_ROOT}/kd_lora_tinymistral_merged

# Copy function code
COPY incar_assist_tod.py ${LAMBDA_TASK_ROOT}/
COPY kd_lora_tinymistral_merged/* ${LAMBDA_TASK_ROOT}/kd_lora_tinymistral_merged/

# Set the handler (file.function)
CMD ["incar_assist_tod.handler"]
