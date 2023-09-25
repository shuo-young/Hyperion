import time
from main import *
from multiprocessing.pool import ThreadPool
import pandas as pd
import logging

if __name__ == '__main__':
    count = 0
    tic = time.time()
    test_list = []
    addresses = pd.read_csv('dataset/925/data.csv', sep="\,", header=None)
    print(addresses)
    for _, (address, platform) in addresses.iterrows():
        data = [address, platform]
        if data not in test_list:
            test_list.append(data)
    # pool = ThreadPool(10)
    # pool.map(batch_analyze_dapp, addr_list)
    for i in test_list:
        log_filename = f"experiment_logset/925/{i[0]}.log"
        logger = logging.getLogger(log_filename)
        handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter(
            '[%(levelname)s][%(filename)s:%(lineno)d]: %(message)s',
            datefmt='%Y.%m.%d. %H:%M:%S',
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        batch_analyze_dapp(i[0], "result/925/", i[1])
        logger.removeHandler(handler)
    toc = time.time()
    log.info('costs: {}s'.format(toc - tic))
