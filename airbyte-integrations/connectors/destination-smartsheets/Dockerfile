FROM python:3.7.11-alpine3.14 as base

# Code Environment Variables
ENV CODE_PATH="destination_smartsheets"

# build and load all requirements 
FROM base as builder
WORKDIR /airbyte/integration_code
COPY $CODE_PATH ./$CODE_PATH

# copy payload code only
COPY main.py ./
COPY setup.py ./

# upgrade pip to the latest version
RUN apk --no-cache upgrade \
    && pip install --upgrade pip


# install necessary packages to a temporary folder 
RUN pip install --prefix=/install .

# build a clean environment  
FROM base
WORKDIR /airbyte/integration_code

# copy all loaded and built libraries to a pure basic image

COPY --from=builder /install /usr/local

# Bash is installed for more convenient debugging.
RUN apk --no-cache add bash



#COPY destination_smartsheets ./destination_smartsheets

ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]

LABEL io.airbyte.version=0.1.0
LABEL io.airbyte.name=airbyte/destination-smartsheets
