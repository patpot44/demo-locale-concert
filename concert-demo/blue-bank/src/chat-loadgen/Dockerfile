FROM locustio/locust:2.43.4

# Break cache with build arg - must be before COPY
ARG CACHEBUST=1
RUN echo "Cachebust: $CACHEBUST"

# Copy the branded locustfile into the image
COPY locustfile.py /locust/locustfile.py

# Set working directory
WORKDIR /locust

# Expose Locust web UI port
EXPOSE 8090

# Default command (can be overridden in deployment)
CMD ["locust", "-f", "/locust/locustfile.py"]