import logging, sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter("[%(levelname)s]:%(name)s:%(message)s"))
logging.info("hello upy")
logging.getLogger("child").info("hello 2")
logging.getLogger("child").debug("hello 2")
