from src.config import kernel_src
from src.utils.log import log_info, log_error, log_success
from singleton_decorator import singleton
import subprocess
import fcntl
import time
import os

_SUCCESS_ID = 'login:'
_TIMEOUT = 300

@singleton
class KernelBooter:
    
    def boot(self, debian_img, bzimage_path, log_file, arch='x86_64'):

        if not os.path.isabs(bzimage_path) and not bzimage_path.startswith(kernel_src):
             bzimage_path = os.path.join(kernel_src, bzimage_path)

        cmd = [
            f'qemu-system-{arch}',
            '-m', '2G',
            '-smp', '2',
            '-kernel', bzimage_path,
            '-append', 'console=ttyS0 earlyprintk=serial,ttyS0 root=/dev/vda1 rw net.ifnames=0',
            '-drive', f'file={debian_img},format=raw,if=virtio',
            '-net', 'user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22',
            '-net', 'nic,model=virtio',
            '-nographic',
            '-pidfile', 'vm.pid',
            '-enable-kvm',
            '-cpu', 'host'
        ]
        
        log_info(f'Starting QEMU boot... Logs: {log_file}')
        log_info(f'Will wait up to {_TIMEOUT} seconds for boot to complete.')

        start_time = time.time()
        success = False

        log_info(f'Approximate endtime is {time.ctime(start_time + _TIMEOUT)}')

        with open(log_file, 'w') as logf:
            proc = None
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=0,
                    text=False,
                    cwd=kernel_src
                )

                fd = proc.stdout.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

                recent_output = ''

                while True:
                    if time.time() - start_time > _TIMEOUT:
                        log_error(f'TIMEOUT reached ({_TIMEOUT}s). Killing QEMU.')
                        break

                    try:
                        data = os.read(fd, 4096)
                        if data:
                            chunk = data.decode('utf-8', errors='ignore')
                            logf.write(chunk)
                            logf.flush()

                            recent_output += chunk
                            if len(recent_output) > 1000:
                                recent_output = recent_output[-1000:]

                            if _SUCCESS_ID in recent_output:
                                log_success('SUCCESS: Found login prompt!')
                                success = True
                                break
                    except BlockingIOError:
                        time.sleep(0.1)

                    if proc.poll() is not None:
                        try:
                            while True:
                                data = os.read(fd, 4096)
                                if not data: break
                                logf.write(data.decode('utf-8', errors='ignore'))
                        except (BlockingIOError, OSError):
                            pass
                        
                        log_error(f'QEMU exited unexpectedly (Code: {proc.returncode}).')
                        break

            except Exception as e:
                log_error(f'Error launching QEMU: {e}')
                logf.write(f'Error launching QEMU: {e}\n')
                if proc:
                    proc.kill()
                return False
            finally:
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()

        if success:
            log_success('QEMU boot SUCCESS.')
        else:
            log_error('QEMU boot FAILED.')

        return success


# def does_boot(commit_hash, bzimage_path):

#     cmd = [
#         'qemu-system-x86_64',
#         '-m', '2G',
#         '-smp', '2',
#         '-kernel', bzimage_path,
#         '-append', 'console=ttyS0 earlyprintk=serial,ttyS0 root=/dev/sda1 rw net.ifnames=0',
#         '-drive', f'file={debian_img_path},format=raw',
#         '-net', 'user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22',
#         '-net', 'nic,model=e1000',
#         '-nographic'
#     ]

#     print(f'Starting QEMU boot for {commit_hash}...')
#     log_file = f'{qemu_log_dir}/{commit_hash}.log'
#     success = False
#     start_time = time.time()

#     with open(log_file, 'w') as logf:
#         proc = None
#         try:
#             proc = subprocess.Popen(
#                 cmd,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.STDOUT,
#                 bufsize=0, 
#                 text=False
#             )

#             recent_output = ''
            
#             while True:
#                 if time.time() - start_time > timeout_seconds:
#                     print(f'TIMEOUT reached ({timeout_seconds}s). Killing QEMU.')
#                     break

#                 if proc.poll() is not None:
#                     print('QEMU exited unexpectedly.')
#                     break

#                 try:
#                     data = os.read(proc.stdout.fileno(), 1024)
#                 except BlockingIOError:
#                     time.sleep(0.1)
#                     continue

#                 if not data:
#                     break

#                 chunk = data.decode('utf-8', errors='ignore')
#                 logf.write(chunk)
#                 logf.flush()

#                 recent_output += chunk
#                 if len(recent_output) > 1000:
#                     recent_output = recent_output[-1000:]

#                 if success_string in recent_output:
#                     print('\nSUCCESS: Found login prompt!')
#                     success = True
#                     break
            
#         except Exception as e:
#             print(f'Error launching QEMU: {e}')
#             if proc: proc.kill()
#             return False, log_file
#         finally:
#             if proc and proc.poll() is None:
#                 proc.terminate()
#                 try:
#                     proc.wait(timeout=2)
#                 except subprocess.TimeoutExpired:
#                     proc.kill()

#     if success:
#         print('QEMU boot SUCCESS.')
#     else:
#         print('QEMU boot FAILED.')

#     return success, log_file

