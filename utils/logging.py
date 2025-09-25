import logging
import os
from pathlib import Path

from discord import utils

logger = logging.getLogger("discord.ciel")


class CustomFilter(logging.Filter):
    def __init__(self, level: int) -> None:
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == logger.name:
            return True
        return record.levelno >= self.level


def setup_logging(develop: bool = False) -> None:
    level = logging.DEBUG if develop else logging.INFO
    log_folder = os.getenv("LOG_FOLDER")
    if log_folder is not None and Path(log_folder).is_dir():
        log_path = Path(log_folder) / "discord.log"
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.addFilter(CustomFilter(level))
        utils.setup_logging(handler=handler, level=logging.DEBUG)
        level = logging.INFO

    handler = logging.StreamHandler()
    handler.addFilter(CustomFilter(level))
    utils.setup_logging(handler=handler, level=logging.DEBUG)
