import logging

# Example 1: Simple use, print to standard output
def example1():
    logging.debug('debug message')
    logging.info('info message')
    logging.warning('warn message')
    logging.error('error message')
    logging.critical('critical message')

# Example 2: Log to a log file
def example2():
    logging.basicConfig(level=logging.DEBUG,filename='/logger.log',format='%(asctime)s :  %(message)s')
    logging.debug('debug message should go to the log file')
    logging.info('info message should go to the log file')
    logging.warning('warn message should go to the log file')
    logging.error('error message should go to the log file')
    logging.critical('critical message should go to the log file')

# Example 3: Record to a log file and print to standard output at the same time
def example3():
    logger=logging.getLogger()

    fh = logging.FileHandler('/logger.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.setLevel(level = logging.DEBUG)
    logger.addHandler(fh)

    logger.debug('debug message')
    logger.info('info message')

if __name__ == "__main__":
    example3()