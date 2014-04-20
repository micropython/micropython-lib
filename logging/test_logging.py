import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("test")
log.debug("Test message: %d(%s)", 100, "foobar")
log.info("Test message2: %d(%s)", 100, "foobar")
