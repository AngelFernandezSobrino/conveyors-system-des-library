import logging

logger = logging.getLogger("main")
logFormatter = logging.Formatter(fmt="%(name)s: %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)
