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
        def percent_to_float(percent_str):
            """Converts a percentage string to a float representation."""
            # Remove commas and percentage signs, then convert to float and divide by 100
            return float(percent_str.replace(',', '').replace('%', '')) / 100

        keywords = ['reward', 'return']
        words = word_tokenize(text)
        tagged = pos_tag(words)
        synonyms = self.get_synonyms(keywords)
        # extend possible words
        synonyms.extend(['roi', 'profit', 'reward/profit', 'apy', 'rewards', 'apr'])
        rewards = {}
        # Daily rate: X% like pattern
        daily_rate_pattern = re.compile(r'daily rate:\s*(\d+\.?\d*)%', re.IGNORECASE)
        matches = daily_rate_pattern.findall(text)
        for match in matches:
            rewards['daily rate'] = percent_to_float(match)

        def search_values(index, direction=1, limit=5):
            values = []
            skip_parenthesis = False
            while limit > 0:
                index += direction
                if index < 0 or index >= len(tagged):
                    break
                if tagged[index][0] == '\n':
                    break
                if tagged[index][0] == '(':
                    skip_parenthesis = True
                elif tagged[index][0] == ')':
                    skip_parenthesis = False
                    index += direction
                    continue
                if skip_parenthesis:
                    index += direction
                    continue
                if tagged[index][1] in ['CD', 'JJ', '%']:
                    if (
                        tagged[index][1] in ['CD', 'JJ']
                        and index + 1 < len(tagged)
                        and tagged[index + 1][0] == '%'
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
                        and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ'])
                        and tagged[k][0] not in ['%', '*']
                    ):
                        fee_type.insert(0, tagged[k][0])
                        k -= 1
                    fee_name = ' '.join(fee_type) + ' ' + word.lower()
                    rewards[fee_name.strip()] = percentages_forward

        return rewards

    # def process_reward(self, text):
    #     keywords = ['reward', 'return']
    #     words = word_tokenize(text)
    #     tagged = pos_tag(words)
    #     synonyms = self.get_synonyms(keywords)
    #     synonyms.extend(['roi', 'rate', 'profit', 'reward/profit'])
    #     rewards = {}
    #     for i, (word, tag) in enumerate(tagged):
    #         if word.lower() in synonyms:
    #             j = i + 1
    #             percentages = []  # List to hold all percentages related to this fee
    #             search_limit = 1  # Limit the search to the next 5 words

    #             # Find all percentages related to this fee
    #             while j < len(tagged) and search_limit > 0:
    #                 # Move j to the next CD or JJ or '%'
    #                 while j < len(tagged) and tagged[j][1] not in ['CD', 'JJ', '%']:
    #                     j += 1
    #                     search_limit -= 1  # Decrement the search limit

    #                 # If j is a number and j+1 is a '%' symbol, save the percentage
    #                 if (
    #                     j < len(tagged)
    #                     and j + 1 < len(tagged)
    #                     and tagged[j + 1][0] == '%'
    #                     and tagged[j][0].replace('.', '').isdigit()
    #                 ):
    #                     percentages.append(tagged[j][0] + "%")
    #                     j += 2  # Move past the percentage symbol
    #                 else:
    #                     break

    #             if percentages:
    #                 fee_type = []
    #                 k = i - 1
    #                 while k >= 0 and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
    #                     fee_type.insert(0, tagged[k][0])
    #                     k -= 1
    #                 fee_name = ' '.join(fee_type) + ' ' + word.lower()
    #                 rewards[
    #                     fee_name.strip()
    #                 ] = percentages  # Save the list of percentages

    #     return rewards  # Return an empty dictionary if no suitable "reward" percentage is found

    # def process_fee(self, text):
    #     keywords = ['fee', 'tax']
    #     words = word_tokenize(text)
    #     tagged = pos_tag(words)
    #     synonyms = self.get_synonyms(keywords)
    #     fees = {}
    #     for i, (word, tag) in enumerate(tagged):
    #         if word.lower() in synonyms:
    #             j = i + 1
    #             percentages = []  # List to hold all percentages related to this fee
    #             search_limit = 1  # Limit the search to the next 5 words

    #             # Find all percentages related to this fee
    #             while j < len(tagged) and search_limit > 0:
    #                 # Move j to the next CD or JJ or '%'
    #                 while j < len(tagged) and tagged[j][1] not in ['CD', 'JJ', '%']:
    #                     j += 1
    #                     search_limit -= 1  # Decrement the search limit

    #                 # If j is a number and j+1 is a '%' symbol, save the percentage
    #                 if (
    #                     j < len(tagged)
    #                     and j + 1 < len(tagged)
    #                     and tagged[j + 1][0] == '%'
    #                     and tagged[j][0].replace('.', '').isdigit()
    #                 ):
    #                     percentages.append(tagged[j][0] + "%")
    #                     j += 2  # Move past the percentage symbol
    #                 else:
    #                     break

    #             if percentages:
    #                 fee_type = []
    #                 k = i - 1
    #                 while k >= 0 and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
    #                     fee_type.insert(0, tagged[k][0])
    #                     k -= 1
    #                 fee_name = ' '.join(fee_type) + ' ' + word.lower()
    #                 fees[fee_name.strip()] = percentages  # Save the list of percentages
    #     return fees
    # def process_fee(self, text):
    #     keywords = [
    #         'buy tax',
    #         'sell tax',
    #         'buy fee',
    #         'sell fee',
    #         'withdrawal fee',
    #         'dev fee',
    #         'marketing fee',
    #         'burn fee',
    #         'transaction fee',
    #         'referral fee',
    #         'deposit fee',
    #         'trade fee',
    #         'tax allocation',
    #         'liquidity fee',
    #     ]
    #     words = word_tokenize(text)
    #     tagged = pos_tag(words)
    #     fees = {}

    #     def search_values(index, direction=1, limit=5):
    #         values = []
    #         skip_parenthesis = False
    #         while limit > 0:
    #             index += direction
    #             if index < 0 or index >= len(tagged):
    #                 break
    #             if tagged[index][0] == '\n':
    #                 break
    #             if tagged[index][0] == '(':
    #                 skip_parenthesis = True
    #             elif tagged[index][0] == ')':
    #                 skip_parenthesis = False
    #                 index += direction
    #                 continue
    #             if skip_parenthesis:
    #                 index += direction
    #                 continue
    #             if tagged[index][1] in ['CD', 'JJ', '%']:
    #                 if (
    #                     tagged[index][1] in ['CD', 'JJ']
    #                     and index + 1 < len(tagged)
    #                     and tagged[index + 1][0] == '%'
    #                 ):
    #                     values.append(tagged[index][0] + "%")
    #                     index += 1
    #             limit -= 1
    #         # return the first found value
    #         if len(values) > 0:
    #             return values[0]
    #         return values

    #     for i, (word, tag) in enumerate(
    #         tagged[:-1]
    #     ):  # We look ahead by one word, hence the -1
    #         keyword = word.lower() + " " + tagged[i + 1][0].lower()
    #         if keyword in keywords:
    #             # First, search forwards until the newline or search limit.
    #             percentages_forward = search_values(
    #                 i + 1, direction=1, limit=4
    #             )  # We start searching after the keyword
    #             # If no values found, search backwards with the limit.
    #             if not percentages_forward:
    #                 percentages_forward = search_values(i, direction=-1, limit=3)

    #             if percentages_forward:
    #                 fees[keyword] = percentages_forward

    #     return fees

    def process_fee(self, text):
        def percent_to_float(percent_str):
            """Converts a percentage string to a float representation."""
            # Remove commas and percentage signs, then convert to float and divide by 100
            return float(percent_str.replace(',', '').replace('%', '')) / 100

        general_keywords = ['fee', 'tax']
        specific_prefixes = [
            'buy',
            'sell',
            'withdrawal',
            'dev',
            'marketing',
            'burn',
            'transaction',
            'referral',
            'deposit',
            'trade',
            'trading',
            'tax',
            'liquidity',
        ]
        specific_suffixes = ['tax', 'fee', 'fees']

        words = word_tokenize(text)
        tagged = pos_tag(words)

        fees_general = {}
        fees_specific = {}

        def search_values(index, direction=1, limit=5):
            values = []
            skip_parenthesis = False
            while limit > 0:
                index += direction
                if index < 0 or index >= len(tagged):
                    break
                if tagged[index][0] == '\n':
                    break
                if tagged[index][0] == '(':
                    skip_parenthesis = True
                elif tagged[index][0] == ')':
                    skip_parenthesis = False
                    index += direction
                    continue
                if skip_parenthesis:
                    index += direction
                    continue
                if tagged[index][1] in ['CD', 'JJ', '%']:
                    if (
                        tagged[index][1] in ['CD', 'JJ']
                        and index + 1 < len(tagged)
                        and tagged[index + 1][0] == '%'
                    ):
                        values.append(percent_to_float(tagged[index][0]))
                        index += 1
                limit -= 1
            # return the first found value
            if len(values) > 0:
                return values[0]
            return values

        for i, (word, tag) in enumerate(tagged[:-1]):
            current_word = word.lower()
            next_word = tagged[i + 1][0].lower()

            # Check if there's a percentage right before the keyword
            if i > 1 and tagged[i - 2][1] in ['CD', 'JJ'] and tagged[i - 1][0] == '%':
                percentage = percent_to_float(tagged[i - 2][0])
            else:
                percentage = None

            # First, match general keywords
            if current_word in general_keywords:
                if not percentage:
                    percentage = search_values(i, direction=1, limit=4)
                    if not percentage:
                        percentage = search_values(i, direction=-1, limit=7)
                if percentage:
                    fee_type = []
                    k = i - 1
                    while k >= 0 and (
                        tagged[k][1] in ['NN', 'NNS', '&', 'JJ']
                        and tagged[k][0] not in ['%', '*']
                    ):
                        fee_type.insert(0, tagged[k][0])
                        k -= 1
                    fee_name = ' '.join(fee_type) + ' ' + word.lower()
                    fees_general[fee_name.strip()] = percentage

            # Then, match specific keywords
            if current_word in specific_prefixes and next_word in specific_suffixes:
                combined_keyword = current_word + " " + next_word
                if not percentage:
                    percentage = search_values(i + 1, direction=1, limit=4)
                    if not percentage:
                        percentage = search_values(i, direction=-1, limit=7)
                if percentage:
                    fees_specific[combined_keyword] = percentage

        return fees_general, fees_specific

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
                    is_number = tagged[j][1] in ['CD', 'JJ'] or tagged[j][0] in [
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
                    while k >= 0 and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
                        lock_description.insert(0, tagged[k][0])
                        k -= 1
                    lock_name = ' '.join(lock_description) + ' ' + word.lower()
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
                    if tagged[j][1] == 'CD':
                        amount = tagged[j][0]
                        j += 1

                        # Handle cases where numbers are written like "275,000,000"
                        while (
                            j < len(tagged)
                            and tagged[j][0] in [',', '.']
                            and j + 1 < len(tagged)
                            and tagged[j + 1][1] == 'CD'
                        ):
                            amount += tagged[j][0] + tagged[j + 1][0]
                            j += 2
                        if j < len(tagged) and (
                            tagged[j][0] == '%' or tagged[j][0] == '.'
                        ):
                            supply_amount = None
                        else:
                            if "," in amount:
                                supply_amount = int(amount.replace(',', ''))
                            else:
                                supply_amount = int(amount)
                        break

                    else:
                        j += 1

                if supply_amount:
                    supply_description = []
                    k = i - 1
                    while k >= 0 and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
                        supply_description.insert(0, tagged[k][0])
                        k -= 1
                    supply_name = ' '.join(supply_description) + ' ' + word.lower()
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


# test case remained
test = """"
  Sure, I'd be happy to help! Based on the text you provided, here are the numerical information related to the rate of fee or tax:

1. Buy fee: 0%
2. Sell fee: 10%
3. Fee is automatically added to LP: 3%

So, the total fee rate is 13% (10% sell fee + 3% fee added to LP)."""
extractor = FrontEndSpecsExtractor()

# for test
fees = extractor.process_fee(test)
# print(fees)
