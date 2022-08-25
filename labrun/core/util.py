import logging
from pkg_resources import resource_filename

def log_config(module_name):
    log = logging.getLogger(module_name)
    log.setLevel(logging.DEBUG)

    # create formatters
    formatter_stderr = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}", datefmt="%H:%M:%S", style="{"
    )
    formatter_file = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}", style="{"
    )

    # create stderr handler
    stderr = logging.StreamHandler()
    stderr.setLevel(logging.INFO)
    stderr.setFormatter(formatter_stderr)

    # create file handler (common log for all modules)
    log_filename = resource_filename("labrun", "logs/common_labrun.log")
    logfile_common = logging.FileHandler(log_filename)
    logfile_common.setLevel(logging.DEBUG)
    logfile_common.setFormatter(formatter_file)

    # create file handler (dedicated log for module)
    log_filename = resource_filename("labrun", f"logs/{module_name}.log")
    logfile_module = logging.FileHandler(log_filename)
    logfile_module.setLevel(logging.DEBUG)
    logfile_module.setFormatter(formatter_file)

    log.addHandler(stderr)
    log.addHandler(logfile_common)
    log.addHandler(logfile_module)
    return log
