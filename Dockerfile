# Use Kali Linux as the base image
FROM kalilinux/kali-rolling

# Set working directory
WORKDIR /app

# Update Kali and install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python2 \
    smbclient \
    nmap \
    curl \
    git \
    && apt-get clean

# Optional: create symlink for python2.7
RUN ln -s /usr/bin/python2 /usr/bin/python2.7 || true

# Copy your app code into the container
COPY . /app

# Install Python dependencies
#RUN pip3 install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 8000

# Start FastAPI app
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
