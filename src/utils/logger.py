from singleton_decorator import singleton

@singleton
class Logger:
    
    def success(self, message: str):
        print(f'[SUCCESS] {message}')

    def info(self, message: str):
        print(f'[INFO] {message}')

    def error(self, message: str):
        print(f'[ERROR] {message}')

log = Logger()
