FROM registry.access.redhat.com/ubi9/nodejs-20:latest
USER root
RUN dnf install -y python3.12 python3.12-pip && dnf clean all && \
    pip3.12 install --no-cache-dir mitmproxy
RUN npm install -g opencode-ai && mkdir -p /workspaces /captures && chown -R 1001:0 /workspaces /captures
COPY entrypoint.sh /usr/local/bin/
COPY export-corpus.py /usr/local/bin/export-corpus.py
RUN chmod +x /usr/local/bin/entrypoint.sh
RUN printf '#!/bin/bash\nexec env -u OPENCODE_SERVER_PASSWORD HOME=/tmp OPENAI_API_KEY=dummy opencode "$@"\n' > /usr/local/bin/dev && chmod +x /usr/local/bin/dev
ENV HOME=/tmp OPENAI_API_KEY=dummy
USER 1001
EXPOSE 3000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]