from enum import Enum
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class BrowserMode(str, Enum):
    DISABLED="disabled"
    LIGHT="light"
    SELENIUM="selenium"
    PLAYWRIGHT="playwright"

class GPUBackend(str, Enum):
    AUTO="auto"
    CUDA="cuda"
    MPS="mps"
    CPU="cpu"

class LogConfig(BaseModel):
    level: str = "INFO"

class OCRConfig(BaseModel):
    backend: GPUBackend = GPUBackend.AUTO
    timeout_s: int = 20

class BrowserConfig(BaseModel):
    mode: BrowserMode = BrowserMode.DISABLED
    page_timeout_s: int = 25

class AppConfig(BaseSettings):
    text_thresh: int = 1000
    max_workers: int = 8
    storage_dir: str = "./data"
    ocr: OCRConfig = OCRConfig()
    browser: BrowserConfig = BrowserConfig()
    log: LogConfig = LogConfig()
    
    class Config:
        env_prefix = "APP__"
        env_nested_delimiter = "__" 