FROM python:3.7-alpine

RUN apk add git && \
    pip install requests

COPY ci-cd-scan.py .

COPY entrypoint.sh /usr/bin/
RUN chmod +x /usr/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]