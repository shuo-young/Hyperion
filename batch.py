import time
from main import *
from multiprocessing.pool import ThreadPool
import pandas as pd
import logging

if __name__ == '__main__':
    count = 0
    tic = time.time()
    # miner_df = pd.read_csv('dataset/miner_test.csv', header=None)
    # miner_list = miner_df[0].tolist()

    # mint_df = pd.read_csv('dataset/mint_test.csv', header=None)
    # mint_list = mint_df[0].tolist()

    # tax_df = pd.read_csv('dataset/tax_test.csv', header=None)
    # tax_list = tax_df[0].tolist()

    # addr_list = miner_list + mint_list + tax_list
    # log.info(addr_list)
    address_1 = pd.read_csv('dataset/924/bsc_1.csv', header=None)
    address_2 = pd.read_csv('dataset/924/bsc_2.csv', header=None)
    address_3 = pd.read_csv('dataset/924/bsc_3.csv', header=None)
    address_4 = pd.read_csv('dataset/924/bsc_4.csv', header=None)
    addr_list = (
        address_1[0].tolist()
        + address_2[0].tolist()
        + address_3[0].tolist()
        + address_4[0].tolist()
    )
    # pool = ThreadPool(10)
    # pool.map(batch_analyze_dapp, addr_list)  # 把任务放入线程池，进行
    for i in addr_list:
        log_filename = f"{i}.log"
        logging.basicConfig(
            filename=log_filename,
            format='[%(levelname)s][%(filename)s:%(lineno)d]: %(message)s',
            datefmt='%Y.%m.%d. %H:%M:%S',
        )
        rootLogger = logging.getLogger(None)

        rootLogger.setLevel(level=logging.DEBUG)
        batch_analyze_dapp(i, "result/924/", "BSC")
    toc = time.time()
    log.info('costs: {}s'.format(toc - tic))
    # process("0x0b98150fe9725e193bfa5ce3e26e2245c61550d4")
