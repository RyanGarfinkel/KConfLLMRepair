FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Update and Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    openjdk-8-jdk \
    gcc \
    git \
    flex \
    bison \
    bc \
    libssl-dev \
    libelf-dev \
    wget \
    unzip \
    xz-utils \
    lftp \
    libjson-java \
    sat4j \
    qemu-system-x86 \
    qemu-system-arm \
    qemu-system-aarch64 \
    gcc-x86-64-linux-gnu && \
    rm -rf /var/lib/apt/lists/*

# Go Setup
RUN wget https://dl.google.com/go/go1.23.6.linux-arm64.tar.gz && \
    tar -xf go1.23.6.linux-arm64.tar.gz && \
    rm go1.23.6.linux-arm64.tar.gz && \
    mv go /usr/local/go

ENV GOROOT=/usr/local/go
ENV PATH=$PATH:$GOROOT/bin

# Z3 Setup
WORKDIR /tmp
COPY z3 /tmp/z3
RUN cd z3 && \
    python3 scripts/mk_make.py --java && \
    cd build && \
    make -j$(nproc)

RUN cp /tmp/z3/build/libz3.so /usr/lib/ && \
    cp /tmp/z3/build/libz3java.so /usr/lib/ && \
    cp /tmp/z3/build/com.microsoft.z3.jar /usr/share/java/ && \
    rm -rf /tmp/z3

ENV LD_LIBRARY_PATH=/usr/lib

# SuperC Setup
WORKDIR /opt
COPY superc /opt/superc

ENV JAVA_DEV_ROOT=/opt/superc
ENV CLASSPATH=$CLASSPATH:$JAVA_DEV_ROOT/classes:$JAVA_DEV_ROOT/bin/superc.jar:$JAVA_DEV_ROOT/bin/xtc.jar:$JAVA_DEV_ROOT/bin/junit.jar:$JAVA_DEV_ROOT/bin/antlr.jar:$JAVA_DEV_ROOT/bin/javabdd.jar:$JAVA_DEV_ROOT/bin/json-simple-1.1.1.jar:/usr/share/java/org.sat4j.core.jar:/usr/share/java/com.microsoft.z3.jar:/usr/share/java/json-lib.jar
ENV JAVA_ARGS="-Xms2048m -Xmx4048m -Xss128m"

RUN cd superc && make configure && make

RUN cat <<'EOF' > /usr/local/bin/superc-linux
#!/bin/sh
exec java $JAVA_ARGS -cp "$CLASSPATH" superc.SuperC "$@"
EOF
RUN chmod +x /usr/local/bin/superc-linux && ln -s /usr/local/bin/superc-linux /usr/local/bin/superc

# KMax Setup
WORKDIR /workspace
COPY kmax /workspace/kmax
RUN python3 -m venv /opt/kmax_env && \
    . /opt/kmax_env/bin/activate && \
    pip install --upgrade pip && \
    pip install ./kmax

RUN echo 'source /opt/kmax_env/bin/activate' >> /root/.bashrc

ENV COMPILER_INSTALL_PATH=$HOME/0day
ENV PATH=$HOME/.local/bin/:$PATH

WORKDIR /workspace

# Syzkaller Setup
WORKDIR /opt
COPY syzkaller /opt/syzkaller
RUN cd /opt/syzkaller && \
    make ARCH=arm64

# Debian Image
WORKDIR /opt
RUN wget https://cloud.debian.org/images/cloud/bullseye/latest/debian-11-generic-arm64.raw

# Run
WORKDIR /workspace
COPY requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt

CMD ["/bin/bash"]
