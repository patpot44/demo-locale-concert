FROM registry.access.redhat.com/ubi9/python-311:latest

# Install locust
RUN pip install --no-cache-dir locust==2.43.4

# Break cache with build arg - must be before COPY
# Cache break: 1782232943
ARG CACHEBUST=1
RUN echo "Cachebust: $CACHEBUST"

# Copy the locustfile and corpus into the image
COPY locustfile.py /app/locustfile.py
COPY corpus.json /app/corpus.json

# Set working directory
WORKDIR /app

# Expose Locust web UI port
EXPOSE 8089

# Default command (can be overridden in deployment)
CMD ["locust", "-f", "/app/locustfile.py"]

# Made with Bob
