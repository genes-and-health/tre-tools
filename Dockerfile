# An official Python runtime as a parent image
FROM python:3.8-slim

# Working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install the package and its dependencies
RUN pip install -e .

# Expose port
EXPOSE 8888

# Set the default command to run when starting the container
CMD ["/bin/bash"]