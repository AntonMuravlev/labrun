import logging
from pkg_resources import resource_filename
from datetime import datetime


def log_config(module_name):

    # disable 3-rd party loggers
    for log_name, log_obj in logging.Logger.manager.loggerDict.items():
        if "labrun" not in log_name:
            log_obj.disabled = True

    #create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # create formatters
    formatter_stderr = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}", datefmt="%H:%M:%S", style="{"
    )
    formatter_file = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}", style="{"
    )
    current_time = datetime.now().strftime("%Y_%m_%d-%H:%M:%S")

    # create stderr handler
    stderr = logging.StreamHandler()
    stderr.setLevel(logging.INFO)
    stderr.setFormatter(formatter_stderr)

    # create file handler (common log for all modules)
    log_filename = resource_filename("labrun", f"logs/{current_time}_common_labrun.log")
    logfile_common = logging.FileHandler(log_filename)
    logfile_common.setLevel(logging.DEBUG)
    logfile_common.setFormatter(formatter_file)

    # create file handler (dedicated log for module)
    log_filename = resource_filename("labrun", f"logs/{current_time}_{module_name}.log")
    logfile_module = logging.FileHandler(log_filename)
    logfile_module.setLevel(logging.DEBUG)
    logfile_module.setFormatter(formatter_file)

    logger.addHandler(stderr)
    logger.addHandler(logfile_common)
    logger.addHandler(logfile_module)
    return logger
