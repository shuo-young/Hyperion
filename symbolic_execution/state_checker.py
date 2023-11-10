import logging
import regex as re

log = logging.getLogger(__name__)


def extract_coefficient_from_division(expr):
    # match outer bvudiv_i function
    pattern = r"bvudiv_i\s*\(\s*((?:[^,()]+|(?R))+)\s*,\s*((?:[^,()]+|(?R))+)\)"
    match = re.search(pattern, expr)

    if not match:
        return None, None

    numerator_expr = match.group(1).strip()
    denominator_expr = match.group(2).strip()

    log.info(numerator_expr)
    log.info(denominator_expr)

    return numerator_expr, denominator_expr


def compute_coefficient(self, expr):
    numerator_expr, denominator_expr = extract_coefficient_from_division(expr)
    if not numerator_expr:
        return None

    # extract coefficient
    coeff_match = re.search(r"^\d+", numerator_expr)
    if coeff_match:
        numerator_expr = coeff_match.group(0)

    numerator_value = self.get_chain_value(numerator_expr)
    if denominator_expr.isdigit():
        denominator_value = int(denominator_expr)
    else:
        denominator_value = self.get_chain_value(denominator_expr)

    # divide 0 case handler
    if denominator_value == 0:
        return float("inf")
    log.info(numerator_value)
    log.info(denominator_value)
    coefficient = numerator_value / denominator_value
    log.info(coefficient)
    return coefficient


# test case remained
contract_address = "0xf7DE7E8A6bd59ED41a4b5fe50278b3B7f31384dF"
expr = "bvudiv_i(Ia_store-14-*\n         bvudiv_i(1000000000000000000*Id_4*mem_mem_64,\n                  1000000000000000000),\n         10000)"
