import logging

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# Create file handler and set level to error
file_handler = logging.FileHandler("error.log", mode="w")
file_handler.setLevel(logging.ERROR)

# Create a formatter
formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s")

# Add formatter to the handlers
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# Log some messages
logger.debug("debug message")
logger.info("info message")
logger.warning("warn message")
logger.error("error message")
logger.critical("critical message")
logger.info("message %s %d", "arg", 5)
logger.info("message %(foo)s %(bar)s", {"foo": 1, "bar": 20})

try:
    1 / 0
except:
    logger.error("Some trouble (%s)", "expected")


# Custom handler example
class MyHandler(logging.Handler):
    def emit(self, record):
        print("levelname=%(levelname)s name=%(name)s message=%(message)s" % record.__dict__)


logging.getLogger().addHandler(MyHandler())
logging.info("Test message7")
