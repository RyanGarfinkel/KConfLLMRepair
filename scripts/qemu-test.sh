WORKING_DIR=$(pwd)

TIMEOUT=300 # 5m
SUCCESS_STRING="login:"

CWD=$1
BZ_IMG=$2
DIR=$3

LOG_FILE=$DIR/qemu.log
rm -f $LOG_FILE

cd $CWD

qemu-system-x86_64 -m 2G -smp 1 -kernel $BZ_IMG \
    -append "console=ttyS0 root=/dev/vda1 ro earlyprintk=serial net.ifnames=0 selinux=0 systemd.mask=networking.service systemd.mask=ifupdown-pre.service systemd.mask=systemd-rfkill.service" \
    -drive file="$DEBIAN_IMG",format=raw,if=virtio \
    -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22 \
    -net nic,model=virtio \
    -device virtio-rng-pci \
    -cpu max \
    -nographic \
    -pidfile "$DIR/qemu.pid" > "$LOG_FILE" 2>&1 &

PID=$!

for i in $(seq 1 $TIMEOUT); do
    if ! kill -0 $PID 2>/dev/null; then
        echo "QEMU process died early!"
        cat "$LOG_FILE"
        cd $WORKING_DIR
        exit 1
    fi
    if grep -q "$SUCCESS_STRING" $LOG_FILE 2>/dev/null; then
        echo "Boot successful! Login prompt detected."
        kill $PID 2>/dev/null || true
        cd $WORKING_DIR
        exit 0
    fi
    sleep 1
done

kill $PID 2>/dev/null || true
echo "Boot failed. Check $LOG_FILE for details."
cd $WORKING_DIR
exit 1