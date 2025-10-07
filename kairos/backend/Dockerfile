# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /code

# Copy the dependencies file to the working directory
COPY ./requirements.txt /code/requirements.txt

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the content of the local src directory to the working directory
COPY ./app /code/app

# Command to run the application
# The command is specified in docker-compose.yml, so no need for CMD here.
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]