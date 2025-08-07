import logging
import logging.config

def setup_logging(level: str = "INFO"):
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "std": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"}
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "std", "level": level}
        },
        "root": {"handlers": ["console"], "level": level},
    })
    return logging.getLogger(__name__) 