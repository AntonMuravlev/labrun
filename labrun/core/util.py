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

    # create file handler
    log_filename = resource_filename("labrun", "logs/all_labrun.log")
    logfile = logging.FileHandler(log_filename)
    logfile.setLevel(logging.DEBUG)
    logfile.setFormatter(formatter_file)


    log.addHandler(stderr)
    log.addHandler(logfile)
    return log
