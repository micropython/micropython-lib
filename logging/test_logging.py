import logging
import os


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


tests = [test_basicConfig]


def test():
    print("Running %i tests." % len(tests))
    for test_function in tests:
        test_function()


if __name__ == '__main__':
    test()
