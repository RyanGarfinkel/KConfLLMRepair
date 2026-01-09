
from dataclasses import dataclass
from typing import Optional

@dataclass
class Sample:
    start_commit: str
    end_commit: str
    patch: str
    config: Optional[str] = None
    build_log: Optional[str] = None
    qemu_boot_result: Optional[bool] = None