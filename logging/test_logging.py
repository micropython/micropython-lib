import logging
import os
import time


def reset_log(log_file):
    try:
        os.remove(log_file)
    except OSError:
        pass


def test_basicConfig():
    print("Testing logging.basicConfig")
    log_file = 'file.log'
    log_message = '123'

    reset_log(log_file)
    logging.basicConfig(filename=log_file)
    logging.info(log_message)

    with open(log_file, 'r') as logf:
        assert log_message in logf.read()

    print("Success: Testing logging.basicConfig")


def stress_test():
    sample = "All work and no play, makes Jack a dull boy!"
    log_file = 'file.log'
    iterations = 100
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

tests = [test_basicConfig]


def test():
    print("Running %i tests." % len(tests))
    for test_function in tests:
        test_function()


if __name__ == '__main__':
    test()
