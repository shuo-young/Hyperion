import re
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import wordnet
import logging

log = logging.getLogger(__name__)


# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')
class FrontEndSpecsExtractor:
    def __init__(self):
        pass

    # analyze dapp frontend docs
    def process_reward(self, text):
        # for reward, we just recover types: daily return, apr, referral reward, while apr is bigger than 1
        def percent_to_float(percent_str):
            """Converts a percentage string to a float representation."""
            # Remove commas and percentage signs, then convert to float and divide by 100
            return float(percent_str.replace(",", "").replace("%", "")) / 100

        keywords = ["reward", "return"]
        words = word_tokenize(text)
        tagged = pos_tag(words)
        synonyms = self.get_synonyms(keywords)
        # extend possible words
        synonyms.extend(["roi", "profit", "apy", "rewards", "apr"])
        rewards = {}

        def search_values(index, direction=1, limit=5):
            values = []
            skip_parenthesis = False
            while limit > 0:
                index += direction
                if index < 0 or index >= len(tagged):
                    break
                if tagged[index][0] == "\n":
                    break
                # skip search limit when meets parenthesis
                if tagged[index][0] == "(":
                    skip_parenthesis = True
                elif tagged[index][0] == ")":
                    skip_parenthesis = False
                    index += direction
                    continue
                if skip_parenthesis:
                    index += direction
                    continue
                if tagged[index][1] in ["CD", "JJ", "%"]:
                    if (
                        tagged[index][1] in ["CD", "JJ"]
                        and index + 1 < len(tagged)
                        and tagged[index + 1][0] == "%"
                    ):
                        values.append(percent_to_float(tagged[index][0]))
                        index += 1
                limit -= 1
            # return the first found value
            if len(values) > 0:
                return values[0]
            return values

        for i, (word, tag) in enumerate(tagged):
            if word.lower() in synonyms:
                # First, search forwards until the newline or search limit.
                percentages_forward = search_values(i, direction=1, limit=4)
                # If no values found, search backwards with the limit.
                if not percentages_forward:
                    percentages_forward = search_values(i, direction=-1, limit=3)

                if percentages_forward:
                    fee_type = []
                    k = i - 1
                    while (
                        k >= 0
                        and (tagged[k][1] in ["NN", "NNS", "&", "JJ"])
                        and tagged[k][0] not in ["%", "*"]
                    ):
                        fee_type.insert(0, tagged[k][0])
                        k -= 1
                    reward_name = " ".join(fee_type) + " " + word.lower()
                    reward_name = reward_name.strip().lower()
                    if percentages_forward <= 1:
                        # first, referral
                        if "referral" in reward_name:
                            reward_name = "referral"
                        # second, roi
                        elif "daily" in reward_name or "yield" in reward_name:
                            reward_name = "roi"
                        # find misused apy and apr:
                        elif "apr" in reward_name or "apy" in reward_name:
                            reward_name = "roi"
                    else:
                        # unify to roi
                        # if (
                        #     "annual" in reward_name
                        #     or "apr" in reward_name
                        #     or "apy" in reward_name
                        # ):
                        reward_name = "roi"
                        percentages_forward = percentages_forward / 365

                    rewards[reward_name] = percentages_forward
        result = {}
        result["reward"] = rewards
        return result

    def process_fee(self, text):
        def percent_to_float(percent_str):
            """Converts a percentage string to a float representation."""
            # Remove commas and percentage signs, then convert to float and divide by 100
            return float(percent_str.replace(",", "").replace("%", "")) / 100

        # define keywords and synonyms
        general_keywords = ["fee", "tax", "fees"]
        general_synonyms = {"fee": ["charge", "cost"], "tax": ["levy", "duty"]}
        # the key prefix can be extended
        specific_prefixes = [
            "buy",
            "sell",
            "selling",
            "deposit",
            "withdrawal",
            "trading",
            "trade",
            "transfer",
            "transaction",
            "dev",
            "marketing",
            "liquidity",
        ]

        # buy, sell, deposit, withdrawal, trade, dev, liquidity
        fee_type_map = {
            "buy": "buy",
            "sell": "sell",
            "selling": "sell",
            "deposit": "deposit",
            "withdrawal": "withdrawal",
            "trading": "trade",
            "trade": "trade",
            "transfer": "trade",
            "transaction": "trade",
            "dev": "dev",
            "marketing": "dev",
            "liquidity": "liquidity",
        }

        # tokenize text
        words = word_tokenize(text)
        tagged = pos_tag(words)

        # initialize result
        has_fee = False
        fees = {}
        fee_values = []  # list to store all fee values found

        def search_values(index, direction=1, limit=5):
            values = []
            skip_parenthesis = False
            while limit > 0:
                index += direction
                if index < 0 or index >= len(tagged):
                    break
                if tagged[index][0] in ["\n", "\r"]:
                    break
                # if tagged[index][0] == "(":
                #     skip_parenthesis = True
                # elif tagged[index][0] == ")":
                #     skip_parenthesis = False
                #     index += direction
                #     continue
                # if skip_parenthesis:
                #     index += direction
                #     continue
                if tagged[index][1] in ["CD", "JJ", "%"]:
                    if (
                        tagged[index][1] in ["CD", "JJ"]
                        and index + 1 < len(tagged)
                        and tagged[index + 1][0] == "%"
                    ):
                        values.append(percent_to_float(tagged[index][0]))

                        index += 1
                limit -= 1
            # return the first found value
            if len(values) > 0:
                return values[0]
            return None

        for i, (word, tag) in enumerate(tagged):
            current_word = word.lower()

            # check if contains general keywords fee/tax
            if current_word in general_keywords:
                percentage = search_values(i, direction=1, limit=6)
                if not percentage:
                    percentage = search_values(i, direction=-1, limit=7)
                if percentage and percentage > 0:
                    has_fee = True
                    fee_values.append(percentage)  # add fee value to the list

            # find fee type
            if current_word in specific_prefixes:
                next_word = tagged[i + 1][0].lower()
                if next_word in general_keywords or next_word in general_synonyms.get(
                    next_word, []
                ):
                    combined_keyword = current_word
                    percentage = search_values(i, direction=1, limit=7)
                    if not percentage:
                        percentage = search_values(i, direction=-1, limit=7)
                    if percentage and percentage > 0:
                        # if combined_keyword not in fees.keys():
                        if combined_keyword.lower() in fee_type_map.keys():
                            fee_general_type = fee_type_map[combined_keyword.lower()]
                        else:
                            fee_general_type = "other"
                        fees[fee_general_type] = percentage
        result = {}
        result["fee"] = {"has_fee": has_fee, "fee_values": fee_values, "fees": fees}
        return result

    def process_lock_time(self, text):
        words = word_tokenize(text)
        tagged = pos_tag(words)
        synonyms = self.get_synonyms(["lock", "locked", "locking"])
        lock_times = {}
        for i, (word, tag) in enumerate(tagged):
            if word.lower() in synonyms:
                j = i + 1
                time_periods = []

                # Find all time periods related to this lock
                while j < len(tagged):
                    # Check if the token is a number (either in digit or word form)
                    is_number = tagged[j][1] in ["CD", "JJ"] or tagged[j][0] in [
                        "one",
                        "two",
                        "three",
                        "four",
                        "five",
                        "six",
                        "seven",
                        "eight",
                        "nine",
                        "ten",
                    ]

                    # If j is a number and j+1 is a time unit, save the time period
                    if (
                        j < len(tagged)
                        and is_number
                        and (
                            tagged[j + 1][0].lower()
                            in ["year", "years", "month", "months", "day", "days"]
                        )
                    ):
                        time_periods.append(tagged[j][0] + " " + tagged[j + 1][0])
                        j += 2
                    else:
                        j += 1  # Continue to the next token

                if time_periods:
                    lock_description = []
                    k = i - 1
                    while k >= 0 and (tagged[k][1] in ["NN", "NNS", "&", "JJ"]):
                        lock_description.insert(0, tagged[k][0])
                        k -= 1
                    lock_name = " ".join(lock_description) + " " + word.lower()
                    # if find, directly return
                    lock_times["lock"] = time_periods
                    return lock_times

        return lock_times

    def process_supply(self, text):
        words = word_tokenize(text)
        tagged = pos_tag(words)
        synonyms = self.get_synonyms(["supply"])
        supplies = {}
        found_total_supply = False
        supply_name = ""

        for i, (word, tag) in enumerate(tagged):
            if word.lower() in synonyms:
                j = i + 1
                supply_amount = None

                # Find all amounts related to this supply keyword
                while j < len(tagged):
                    if tagged[j][1] == "CD":
                        amount = tagged[j][0]
                        j += 1

                        # Handle cases where numbers are written like "275,000,000"
                        while (
                            j < len(tagged)
                            and tagged[j][0] in [",", "."]
                            and j + 1 < len(tagged)
                            and tagged[j + 1][1] == "CD"
                        ):
                            amount += tagged[j][0] + tagged[j + 1][0]
                            j += 2
                        if j < len(tagged) and (
                            tagged[j][0] == "%" or tagged[j][0] == "."
                        ):
                            supply_amount = None
                        else:
                            if "," in amount:
                                supply_amount = int(amount.replace(",", ""))
                            else:
                                supply_amount = int(amount)
                        break

                    else:
                        j += 1

                if supply_amount:
                    supply_description = []
                    k = i - 1
                    while k >= 0 and (tagged[k][1] in ["NN", "NNS", "&", "JJ"]):
                        supply_description.insert(0, tagged[k][0])
                        k -= 1
                    supply_name = " ".join(supply_description) + " " + word.lower()
                    supplies[supply_name.strip()] = supply_amount

                # Check if the current supply keyword is "total supply"
                if "total supply" in supply_name.strip().lower():
                    found_total_supply = True

                # If "total supply" was found and the supply amount is not None, return it
                if found_total_supply and supply_amount is not None:
                    return {"supply": supply_amount}

        return supplies

    def process_bool(self, text, type):
        sentences = sent_tokenize(text)
        answer_sentences = [
            sentence for sentence in sentences if "answer" in sentence.lower()
        ]
        if answer_sentences:
            answer_sentence = answer_sentences[0]
            answer = answer_sentence.split("answer is", 1)[-1].strip()
            if "no" in answer.lower():
                answer = False
            elif "yes" in answer.lower():
                answer = True
            else:
                answer = False
            return {type: answer}
        else:
            # if no findings, return False by default
            return {type: False}

    def get_synonyms(self, keywords):
        # keywords = ['fee']
        synonyms = keywords[:]
        for keyword in keywords:
            for syn in wordnet.synsets(keyword):
                for lemma in syn.lemmas():
                    synonyms.append(lemma.name())

        # remove duplicated
        synonyms = list(set(synonyms))
        return synonyms
