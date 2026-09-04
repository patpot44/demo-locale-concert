FROM registry.access.redhat.com/ubi9/python-311:latest
WORKDIR /app
RUN pip install --no-cache-dir flask langchain-openai httpx
COPY app.py .
EXPOSE 5001
CMD ["python", "app.py"]