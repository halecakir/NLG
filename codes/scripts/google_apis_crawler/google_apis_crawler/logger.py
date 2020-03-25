import logging
from logging.config import dictConfig

LOGGING_CONFIG = dict(
    disable_existing_loggers=False,
    version=1,
    formatters={"standard": {"format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"}},
    handlers={
        'default': { 
            'level': logging.ERROR,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'file': {
            "level": logging.ERROR,
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "out.log",
            "mode": "w",
        },
    },
    loggers={
        '': {
            'handlers': ['default'],
            'level': 'ERROR',
            'propagate': False
        },
        'database': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False
        }
    }
)

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("database")
