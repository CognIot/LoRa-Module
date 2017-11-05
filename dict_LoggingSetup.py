"""
Logging Configuration File
Levels
- CRITICAL
- ERROR
- WARNING
- INFO
- DEBUG
"""

import logging


log_cfg = dict(
    version = 1,
    formatters = {
        'full': {'format':
              '%(asctime)s - %(levelname)-8s - %(message)s',
              },
        'brief': {'format':
              '%(asctime)s - %(message)s',
              'datefmt': '%d-%m-%Y %H:%M:%S'}
        },
    handlers = {
        'screen': {'class': 'logging.StreamHandler',
              'formatter': 'brief',
              'level': logging.ERROR,
              'stream': 'ext://sys.stdout'},
              
        'file': {'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'full',
                'level': logging.DEBUG,
                'filename': 'CognIoT.log',
                'maxBytes':  1638400,
                'backupCount' : 5,
                'mode': 'w'},
                  
        },
    root = {
        'handlers': ['screen', 'file'],
        'level': logging.DEBUG,
        },
        )
