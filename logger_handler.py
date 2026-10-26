import logging
from utils.path_tool import get_abs_path
import os
from datetime import datetime

"""日志配置，定义get_logger方法，并在最后提供一个logger供全局调用"""
"""
代码是搭管道、装阀门；触发消息、过滤、输送输出，都是 logging 内部自带的能力。
logger作用：给程序装一套"可配置的记录系统"：谁想记一笔，就调 logger，它按代码配的级别过滤、按代码配的去向（控制台/文件）输出。 
代码配 handler 和分级，就是在定义"记多细、记到哪、记成什么样"。
代码控制的结果就是普通 debug 日志不打印控制台，info 还有比他高的会打印在控制台，所有的都可以写在日志文件保存

Handler是处理器，决定日志往哪里输出，Logger负责生产日志消息
1.代码里有两个Handler：
-> console_handler: 输出打印在控制台，给开发实时看
-> file_handler：写在文件里，事后看

2.设置两道level：目的是让控制台日志打印干净
两个Handler有不同级别，
日志级别 → 过总闸(DEBUG) → 过控制台分闸(INFO) → 显示
                          ↘ 过文件分闸(DEBUG) → 落盘
                          
console_handler = logging.StreamHandler()  控制输出到控制台上的处理器，级别是INFO
file_handler = logging.FileHandler(log_file, encoding='utf-8')  控制写到文件的处理器，级别是DEBUG

3.为什么 if logger.handlers: return logger
不判断的话，同一个名字的 logger 每次 get_logger() 都重新 addHandler，一条日志会被打两遍甚至多遍。这一行就是防止重复挂载。
- 如果列表不为空（里面已经有 StreamHandler、FileHandler 了） → 条件成立，直接 return，不再新增 handler
- 如果列表是空 [] → 条件不成立，往下走，去创建并且添加控制台、文件 handler
"""

# 日志保存的根目录
LOG_ROOT = get_abs_path("logs")

# 确保日志的目录存在
os.makedirs(LOG_ROOT, exist_ok=True)

# 日志的格式配置  error info debug
DEFAULT_LOG_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)


def get_logger(
        name: str = "agent",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加Handler
    if logger.handlers:
        return logger

    # 控制台Handler
    console_handler = logging.StreamHandler()# 控制输出到控制台的Handler，级别为console_level,是INFO，文件handler级别低于这个，所以不会输出到控制台上
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)

    logger.addHandler(console_handler)

    # 文件Handler
    if not log_file:        # 日志文件的存放路径
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)

    logger.addHandler(file_handler)

    return logger


# 快捷获取日志器，全局使用
logger = get_logger()


if __name__ == '__main__':
    logger.info("信息日志")
    logger.error("错误日志")
    logger.warning("警告日志")
    logger.debug("调试日志")
