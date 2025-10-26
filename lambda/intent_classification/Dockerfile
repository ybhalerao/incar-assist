# Use AWS Lambda Python 3.10 base
FROM public.ecr.aws/lambda/python:3.13

# Install system deps (strip is handy for size trimming; optional)
#RUN yum -y install binutils && yum clean all

# Copy and install Python deps
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Make the directories
RUN mkdir ${LAMBDA_TASK_ROOT}/roberta-student-distilled

# Copy function code
COPY incar_assist_ic.py ${LAMBDA_TASK_ROOT}/
COPY /roberta-student-distilled/* ${LAMBDA_TASK_ROOT}/roberta-student-distilled/

# Set the handler (file.function)
CMD ["incar_assist_ic.handler"]
