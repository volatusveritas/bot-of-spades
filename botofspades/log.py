import logging


logger: logging.Logger = logging.getLogger("botofspades")


def setup_logging() -> None:
    formatter: logging.Formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s"
    )

    handler: logging.StreamHandler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def extension_loaded(name: str) -> None:
    logger.info(f"Extension loaded: {name}")


def extension_unloaded(name: str) -> None:
    logger.info(f"Extension unloaded: {name}")
