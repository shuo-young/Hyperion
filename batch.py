import os
from main import *
from multiprocessing.pool import ThreadPool
import pandas as pd
import logging

if __name__ == '__main__':
    count = 0
    tic = time.time()
    miner_df = pd.read_csv('miner_test.csv', header=None)
    miner_list = miner_df[0].tolist()

    mint_df = pd.read_csv('mint_test.csv', header=None)
    mint_list = mint_df[0].tolist()

    tax_df = pd.read_csv('tax_test.csv', header=None)
    tax_list = tax_df[0].tolist()

    addr_list = miner_list + mint_list + tax_list
    print(addr_list)

    logging.basicConfig(
        format='[%(levelname)s][%(filename)s:%(lineno)d]: %(message)s',
        datefmt='%Y.%m.%d. %H:%M:%S',
    )
    rootLogger = logging.getLogger(None)

    rootLogger.setLevel(level=logging.DEBUG)

    # pool = ThreadPool(10)
    # pool.map(batch_analyze_dapp, addr_list)  # 把任务放入线程池，进行
    for i in addr_list:
        batch_analyze_dapp(i)
    toc = time.time()
    print('costs: {}s'.format(toc - tic))
    # process("0x0b98150fe9725e193bfa5ce3e26e2245c61550d4")
