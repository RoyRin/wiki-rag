FROM amazonlinux:2

# Install Python 3 & pip
RUN yum install -y python3 python3-pip \
 && yum clean all

WORKDIR /app
COPY server.py .

ENTRYPOINT ["python3", "/app/server.py"]
