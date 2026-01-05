FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-dev python3-pip pipx \
    gcc build-essential make \
    flex bison bc \
    libssl-dev libelf-dev \
    git wget unzip xz-utils lftp \
    openjdk-8-jdk \
    qemu-system-x86 \
    clang-15 llvm-15 lld-15 dwarves \
    libz3-java libjson-java sat4j lz4 zstd libdw-dev \
    gcc-x86-64-linux-gnu binutils-x86-64-linux-gnu && \
    update-alternatives --install /usr/bin/clang clang /usr/bin/clang-15 100 && \
    update-alternatives --install /usr/bin/ld.lld ld.lld /usr/bin/ld.lld-15 100 && \
    rm -rf /var/lib/apt/lists/*

# Go installation
RUN ARCH=$(dpkg --print-architecture) && \
    wget https://dl.google.com/go/go1.24.4.linux-${ARCH}.tar.gz && \
    tar -xf go1.24.4.linux-${ARCH}.tar.gz && \
    rm go1.24.4.linux-${ARCH}.tar.gz && \
    mv go /usr/local/go

ENV GOROOT=/usr/local/go
ENV PATH=$PATH:$GOROOT/bin

# Dev user setup
RUN useradd -m dev

USER dev

# Env variables & copies directories
ENV HOME=/home/dev \
    PATH=/home/dev/.local/bin:$PATH \
    DEBIAN_IMG_SRC=/home/dev/opt/debian.raw \
    KERNEL_SRC=/home/dev/opt/kernel \
    SYZKALLER_SRC=/home/dev/opt/syzkaller \
    Z3_SRC=/home/dev/opt/z3

WORKDIR $HOME/opt
COPY --chown=dev:dev debian.raw $DEBIAN_IMG_SRC
COPY --chown=dev:dev kernel $KERNEL_SRC
COPY --chown=dev:dev syzkaller $SYZKALLER_SRC
COPY --chown=dev:dev z3 $Z3_SRC

RUN git config --global --add safe.directory /home/dev/opt/kernel && \
    git config --global --add safe.directory /home/dev/opt/syzkaller

# Syzkaller installation
WORKDIR $SYZKALLER_SRC
RUN make

ENV PATH=$SYZKALLER_SRC/bin:$PATH

# Z3 installation
WORKDIR $Z3_SRC
RUN python3 scripts/mk_make.py --java
WORKDIR $Z3_SRC/build
RUN make -j4$(nproc)

ENV CLASSPATH=/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:$Z3_SRC/build/com.microsoft.z3.jar:$CLASSPATH
ENV LD_LIBRARY_PATH=$Z3_SRC/build:$LD_LIBRARY_PATH

# SuperC installation
RUN wget -O - https://raw.githubusercontent.com/appleseedlab/superc/master/scripts/install.sh | bash
ENV CLASSPATH=$HOME/.local/share/superc/superc.jar:$HOME/.local/share/superc/xtc.jar:$HOME/.local/share/superc/JavaBDD/javabdd-1.0b2.jar:/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:$Z3_SRC/build/com.microsoft.z3.jar:$CLASSPATH

# Python tools installation
WORKDIR /workspace
COPY requirements.txt /workspace/requirements.txt
RUN pipx install kmax && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt

CMD ["/bin/bash"]
