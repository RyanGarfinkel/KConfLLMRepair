#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
BZ_IMG=$2
LOG_FILE=$3
TIMEOUT=${4:-600} # 10m Default

# Variables
SUCCESS_STRING='login:'
MAINTENANCE_STRING='Press Enter for maintenance'

# Running QEMU
rm -f "$LOG_FILE"
cd "$WORKING_DIR"

qemu-system-x86_64 -m 2G -smp 1 -kernel "$BZ_IMG" \
    -append "console=ttyS0 root=/dev/sda1 rw init=/sbin/init earlyprintk=serial net.ifnames=0 selinux=0" \
    -drive file="$DEBIAN_IMG",format=raw \
    -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22 \
    -net nic,model=e1000 \
    -cpu max \
    -nographic > "$LOG_FILE" 2>&1 &

# qemu-system-x86_64 \
#     -m 2G \
#     -smp 2 \
#     -kernel "$BZ_IMG" \
#     -append "console=ttyS0 root=/dev/sda earlyprintk=serial net.ifnames=0" \
#     -drive file="$DEBIAN_IMG",format=raw \
#     -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22 \
#     -net nic,model=e1000 \
#     -enable-kvm \
#     -nographic > "$LOG_FILE" 2>&1 &

# Waiting for Login Prompt
PID=$!

for i in $(seq 1 $TIMEOUT); do
    if ! kill -0 $PID 2>/dev/null; then
        echo '[ERROR] QEMU process died early!'
        cd "$WORKING_DIR"
        exit 1
    fi
    if grep -q "$SUCCESS_STRING" "$LOG_FILE" 2>/dev/null; then
        echo '[SUCCESS] Boot successful! Login prompt detected.'
        kill $PID 2>/dev/null || true
        cd "$WORKING_DIR"
        exit 0
    fi
    if grep -q "$MAINTENANCE_STRING" "$LOG_FILE" 2>/dev/null; then
        echo '[SUCCESS] Boot successful! Emergency maintenance prompt detected.'
        kill $PID 2>/dev/null || true
        cd "$WORKING_DIR"
        exit 0
    fi
    sleep 1
done

kill $PID 2>/dev/null || true
echo "[ERROR] Boot failed. Check $LOG_FILE for details."
cd "$WORKING_DIR"
exit 1
