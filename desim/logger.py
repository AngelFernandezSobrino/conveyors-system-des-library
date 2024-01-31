import logging

LOGGER_STOPPER_COLOR: str = "\N{ESC}[36m"
LOGGER_CONVEYOR_COLOR: str = "\N{ESC}[33m"

LOGGER_INPUT_EVENT_COLOR: str = "\N{ESC}[32m"
LOGGER_OUTPUT_EVENT_COLOR: str = "\N{ESC}[31m"
LOGGER_STATE_CHANGE_COLOR: str = "\N{ESC}[34m"

LOGGER_BASE_NAME: str = "desim"
LOGGER_STOPPER_NAME: str = "stop"
LOGGER_CONVEYOR_NAME: str = "conv"

LOGGER_INPUT_GROUP_NAME: str = "Input "
LOGGER_OUTPUT_GROUP_NAME: str = "Output"
LOGGER_STATE_GROUP_NAME: str = "State "

LOGGER_NAME_PADDING: int = 11


def get_logger(name: str, formater_without_message: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False
    logFormatter = logging.Formatter(
        formater_without_message + "{message}",
        style="{",
    )
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    logger.debug("created")
    return logger
