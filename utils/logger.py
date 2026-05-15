import logging
import os
from datetime import datetime

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件名按小时分割，避免单文件过大
log_file = os.path.join(LOG_DIR, f"crawler_{datetime.now().strftime('%Y%m%d_%H')}.log")

logger = logging.getLogger("douban_crawler")
logger.setLevel(logging.INFO)
logger.propagate = False  # 避免重复输出

# 日志格式增强（添加模块名、行号）
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 文件处理器（按大小轮转）
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)