FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential make gcc g++ \
    flex bison bc \
    libssl-dev libelf-dev libncurses-dev dwarves \
    python3 python3-dev python3-pip python3-venv pipx lz4 \
    git wget unzip xz-utils lftp default-jdk \
    openjdk-8-jdk libz3-java libjson-java sat4j \
    qemu-system-x86 libdw-dev ccache \
    clang-18 llvm-18 lld-18 \
    gcc-x86-64-linux-gnu \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 100 \
    && update-alternatives --install /usr/bin/ld.lld ld.lld /usr/bin/ld.lld-18 100

# Go
ENV GOROOT=/opt/go
ENV PATH=$GOROOT/bin:$PATH
RUN wget -q https://go.dev/dl/go1.24.4.linux-amd64.tar.gz -O /tmp/go.tar.gz \
    && tar -C /opt -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

# Syzkaller
ENV SYZKALLER_SRC=/opt/tools/syzkaller
ENV SYZ_KCONF=/opt/tools/syzkaller/bin/syz-kconf
ENV MAIN_YML=/opt/tools/syzkaller/dashboard/config/linux/main.yml
RUN git clone --depth 1 https://github.com/google/syzkaller.git $SYZKALLER_SRC \
    && cd $SYZKALLER_SRC && make && make kconf

# Z3
ENV Z3_SRC=/opt/tools/z3
ENV LD_LIBRARY_PATH=$Z3_SRC/build:/root/.local/lib
RUN git clone --branch z3-4.8.17 --depth 1 https://github.com/Z3Prover/z3.git $Z3_SRC \
    && cd $Z3_SRC \
    && python3 scripts/mk_make.py --java \
    && cd build && make -j$(nproc)

# SuperC
RUN mkdir -p /tmp/superc-install \
    && cd /tmp/superc-install \
    && wget -O - https://raw.githubusercontent.com/appleseedlab/superc/master/scripts/install.sh | bash \
    && rm -rf /tmp/superc-install
ENV SUPERC_PATH=/root/.local/bin/superc_linux.sh
ENV CLASSPATH=/root/.local/share/superc/superc.jar:/root/.local/share/superc/xtc.jar:/root/.local/share/superc/JavaBDD/javabdd-1.0b2.jar:/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:/opt/tools/z3/build/com.microsoft.z3.jar

# Linux Kernel
ENV KERNEL_SRC=/opt/kernel
RUN git clone --depth 1 --branch v6.19 \
    https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git $KERNEL_SRC

# Python Venv, Dependencies, KMax
ENV VIRTUAL_ENV=/opt/venv
ENV PATH=$VIRTUAL_ENV/bin:/usr/lib/ccache:$PATH
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv $VIRTUAL_ENV \
    && pip install --upgrade pip setuptools \
    && pip install -r /tmp/requirements.txt \
    && git clone --branch dev/klocalizer-add-check-mutex --depth 1 \
        https://github.com/paulgazz/kmax.git /tmp/kmax \
    && cd /tmp/kmax && pip install --no-build-isolation . \
    && rm -rf /tmp/kmax /tmp/requirements.txt

ENV CPLUS_INCLUDE_PATH=/root/.local/include:/root/.local/include/elfutils
ENV C_INCLUDE_PATH=/root/.local/include:/root/.local/include/elfutils
ENV CROSS_COMPILE=x86_64-linux-gnu-
ENV LIBRARY_PATH=/root/.local/lib
ENV ARCH=x86_64
