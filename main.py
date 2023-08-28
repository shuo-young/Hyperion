import argparse
from datetime import datetime
from web3 import Web3

import time
from global_params import *


from nlp.nlp import FrontEndSpecsExtractor
from semantic_parser.semantic import Semantics


if __name__ == '__main__':
    # Main Body
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-du",
        "--dapp_url",
        help="The url of the tested dapp.",
        action="store",
        dest="dapp_url",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--address",
        help="Contract address of the dapp",
        action="store",
        dest="addr",
        type=str,
    )
    parser.add_argument(
        "-bp",
        "--blockchain_platform",
        help="The blockchain platform where the dapp contract is deployed",
        action="store",
        dest="platform",
        type=str,
        default="ETH",
    )
    parser.add_argument(
        "-bn",
        "--block_number",
        help="Tested blockchain snapshot",
        action="store",
        dest="block_number",
        type=int,
        default=16000000,
    )
    args = parser.parse_args()

    # NLP process
    # extract_specs_helper = FrontEndSpecsExtractor(args.dapp_url)
    # specs = extract_specs_helper.process()

    # Backend contract analysis
    source = {
        "platform": args.platform,
        "address": args.addr,
        "block_number": args.block_number,
    }
    begin = time.perf_counter()

    # Analyzer
    semantic = Semantics(
        source["platform"],
        source["address"],
        source["block_number"],
    )
