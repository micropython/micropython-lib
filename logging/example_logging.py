import os
import time
import logging


def reset_log(log_file):
    try:
        os.remove(log_file)
    except OSError:
        pass


def stress_test(iterations):
    sample = "All work and no play, makes Jack a dull boy!"
    log_file = 'file.log'
    reset_log(log_file)
    logging.basicConfig(filename=log_file)
    start_time = time.time()
    for i in range(iterations):
        logging.info("%d %s" % (i, sample))
    file_delta = time.time() - start_time
    reset_log(log_file)

    logging.basicConfig(filename=None)
    start_time = time.time()
    for i in range(iterations):
        logging.info("%d %s" % (i, sample))
    stdout_delta = time.time() - start_time
    print("File logging time %f for %i iterations" % (file_delta, iterations))
    print("Stdout logging time %f for %i iterations" % (stdout_delta, iterations))


logging.basicConfig(level=logging.INFO)
log = logging.getLogger("test")
log.debug("Test message: %d(%s)", 100, "foobar")
log.info("Test message2: %d(%s)", 100, "foobar")

#stress_test(100)