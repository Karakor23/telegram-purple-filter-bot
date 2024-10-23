import logging
import sys

def setup_logger(name):
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        stream=sys.stdout
    )
    return logging.getLogger(name)