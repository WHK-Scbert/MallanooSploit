# Use Kali Linux as the base image
FROM kalilinux/kali-rolling

# Set working directory
WORKDIR /app

# Update Kali and install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3.13-venv \
    python2 \
    smbclient \
    nmap \
    curl \
    git \
    net-tools \
    && apt-get clean

# Optional: create symlink for python2.7
RUN ln -s /usr/bin/python2 /usr/bin/python2.7 || true

# Copy your app code into the container
COPY . /app

# Set up Python virtual environment
RUN python3 -m venv /app/env

# Activate virtual environment and install Python dependencies
RUN /bin/bash -c "source /app/env/bin/activate && pip install --upgrade pip && pip install -r /app/API/requirements.txt"

# Expose API port
EXPOSE 8000

# Start FastAPI app automatically
CMD ["/bin/bash", "-c", "source /app/env/bin/activate && uvicorn app:app --reload --host 0.0.0.0 --port 8000"]
