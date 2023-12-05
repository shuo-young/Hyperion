import argparse
import json
import logging

from global_params import *
import symbolic_execution.ir_se
from symbolic_execution.ir_se import *


from nlp.text_analyzer import FrontEndSpecsExtractor
from semantic_parser.semantic import Semantics
from symbolic_execution.state_extractor import StateExtractor


def analyze_dapp():
    global args
    log.info("Begin processing text info...")
    # NLP process
    # extract_specs_helper = FrontEndSpecsExtractor(args.dapp_text)
    # specs = extract_specs_helper.process()
    log.info("Complete processing text info...")
    log.info("Begin processing contract " + args.addr + "...")
    # Backend contract analysis
    source = {
        "platform": args.platform,
        "address": args.addr,
        "block_number": args.block_number,
    }

    # Analyzer
    # semantic covers the targeted functions, storage of the critical state variable
    semantic = Semantics(
        source["platform"],
        source["address"],
        source["block_number"],
    )
    inputs = semantic.get_inputs()[0]
    exit_code = 0

    # initialize state extractor for rate determination
    state_extractor = StateExtractor(
        source["platform"],
        source["address"],
        source["block_number"],
    )

    result, exit_code = symbolic_execution.ir_se.run(inputs, state_extractor)
    log.info("Complete processing contract...")
    result["metadata"] = semantic.storage_way
    result["supply"]["amount"] = semantic.supply_amount
    result["dapp_name"] = args.dapp_name
    result["address"] = source["address"]
    result["platform"] = source["platform"]
    log.info(result)
    json_str = json.dumps(result, default=complex_handler, indent=4)
    filename = args.output_dir + "/" + source["address"] + ".json"
    with open(filename, "w") as file:
        file.write(json_str)
    return exit_code


def complex_handler(obj):
    if isinstance(obj, BitVecRef):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def main():
    global args
    # Main Body
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-dt",
        "--dapp_text",
        help="The text information of the tested dapp.",
        action="store",
        dest="dapp_text",
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
    parser.add_argument(
        "-v", "--verbose", help="Verbose output, print everything.", action="store_true"
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Dapp name.",
        action="store",
        dest="dapp_name",
        type=str,
        default="",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Output directory path.",
        action="store",
        dest="output_dir",
        type=str,
        default="result",
    )
    args = parser.parse_args()

    logging.basicConfig(
        format="[%(levelname)s][%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y.%m.%d. %H:%M:%S",
    )
    rootLogger = logging.getLogger(None)

    if args.verbose:
        rootLogger.setLevel(level=logging.DEBUG)
    else:
        rootLogger.setLevel(level=logging.INFO)

    exit_code = analyze_dapp()
    exit(exit_code)


if __name__ == "__main__":
    main()
