OUTPUT_PATH = "./gigahorse-toolchain/"

JSON_PATH = "./output/"

CONTRACT_PATH = "./gigahorse-toolchain/contracts/"

CONTRACT_DIR = "./contracts/"

TEMP_WORKING_DIR = "./gigahorse-toolchain/.temp/"

"""Global configuration variables for running program"""

# enable reporting of the result
REPORT_MODE = 0

# print everything in the console
PRINT_MODE = 0

# enable log file to print all exception
DEBUG_MODE = 0

# Timeout for z3 in ms
TIMEOUT = 3000

# Set this flag to 2 if we want to do evm real value unit test
# Set this flag to 3 if we want to do evm symbolic unit test
UNIT_TEST = 0

# timeout to run symbolic execution (in secs)
GLOBAL_TIMEOUT = 600

# timeout to run symbolic execution (in secs) for testing
GLOBAL_TIMEOUT_TEST = 2

# print path conditions
PRINT_PATHS = 0

# Redirect results to a json file.
STORE_RESULT = 1

# depth limit for DFS
DEPTH_LIMIT = 500

GAS_LIMIT = 400000000

LOOP_LIMIT = 200

GENERATE_TEST_CASES = 0

# Run NFTGuard in parallel
PARALLEL = 0

TARGET_CONTRACTS = None
