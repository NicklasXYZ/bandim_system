# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

# Set environment variables:
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /code

# Install dependencies
RUN pip install fastapi \
    uvicorn[standard] \
    sqlmodel \
    pydantic \
    redis \
    scipy \
    numpy \
    pandas \
    scikit-learn \
    matplotlib

# Copy the current directory contents into the container at /code
COPY ./bandim-api /code

# Command to run the uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
