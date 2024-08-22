# Use an official Python runtime as a parent image
FROM ghcr.io/translatorsri/renci-python-image:3.12.4

#Build from this branch.  Assume master for this repo
ARG BRANCH_NAME=main

# update the container
RUN apt-get update
RUN apt install git

# make a directory for the repo
RUN mkdir /repo

# go to the directory where we are going to upload the repo
WORKDIR /repo

# get the latest code
RUN git clone --branch $BRANCH_NAME --single-branch https://github.com/wumirose/Edgar.git


# go to the repo dir
WORKDIR /repo/Edgar


RUN chmod 777 -R .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

RUN pip install uvicorn

# switch to the non-root user (nru). defined in the base image
USER nru

# Make port 8050 available to the world outside this container
EXPOSE 8050

## Define environment variable
#ENV NAME DashApp

# Run app.py when the container launches
CMD ["python", "app.py"]