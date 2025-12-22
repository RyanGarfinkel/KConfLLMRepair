import subprocess
import time

debian_img_path = '/opt/debian-11-generic-arm64.raw'
success_string = 'login:'

def does_boot(bzimage_path, timeout_seconds=300, qemu_log_path='vm.log'):
    
    cmd = [
        'qemu-system-x86_64',
        '-m', '2G',
        '-smp', '2',
        '-kernel', bzimage_path,
        '-append', 'console=ttyS0 root=/dev/sda earlyprintk=serial net.ifnames=0',
        '-drive', f'file={debian_img_path},format=raw',
        '-net', 'user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22',
        '-net', 'nic,model=e1000',
        '-enable-kvm',
        '-nographic'
    ]

    print('Starting QEMU to boot kernel...')
    with open(qemu_log_path, 'w') as logf:
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=logf,
                stderr=subprocess.STDOUT
            )

            t0 = time.time()
            while proc.poll() is None and (time.time() - t0) < timeout_seconds:
                time.sleep(2)
            if proc.poll() is None:
                print(f'Timeout reached ({timeout_seconds}s), killing QEMU...')
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
            exit_code = proc.poll()
        except Exception as e:
            print('Error launching QEMU:', e)
            return False

    boot_successful = False
    with open(qemu_log_path, 'r') as logf:
        lines = logf.readlines()
        for line in lines:
            if success_string in line:
                boot_successful = True
                break

    if boot_successful:
        print('SUCCESS: Found success string in QEMU output (login prompt reached).')
    else:
        print('FAILED: Did not find success string in QEMU output.')
    print(f'QEMU exit code: {exit_code}')
    return boot_successful

bzimage = '/absolute/path/to/bzImage'
debian_img = '/absolute/path/to/debian.img'
result = does_boot(bzimage)