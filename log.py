import logging

# create logger
logger = logging.getLogger('transaction_logger')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.FileHandler('transactions.log')
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
