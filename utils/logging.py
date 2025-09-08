import logging
import os
from pathlib import Path

from discord import utils

logger = logging.getLogger("discord.ciel")


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    log_folder = os.getenv("LOG_FOLDER")
    if log_folder and Path(log_folder).is_dir():
        log_path = Path(log_folder) / "discord.log"
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(level)
        utils.setup_logging(handler=handler, level=logging.DEBUG)
        level = logging.INFO

    handler = logging.StreamHandler()
    handler.setLevel(level)
    utils.setup_logging(handler=handler, level=logging.DEBUG)
