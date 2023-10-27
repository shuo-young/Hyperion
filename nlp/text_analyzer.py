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
    def process_reward1(self, text):
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
            rewards['daily rate'] = match + "%"

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
                        values.append(tagged[index][0] + "%")
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
                    while k >= 0 and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
                        fee_type.insert(0, tagged[k][0])
                        k -= 1
                    fee_name = ' '.join(fee_type) + ' ' + word.lower()
                    rewards[fee_name.strip()] = percentages_forward

        return rewards

    def process_reward(self, text):
        keywords = ['reward', 'return']
        words = word_tokenize(text)
        tagged = pos_tag(words)
        synonyms = self.get_synonyms(keywords)
        synonyms.extend(['roi', 'rate', 'profit', 'reward/profit'])
        rewards = {}
        for i, (word, tag) in enumerate(tagged):
            if word.lower() in synonyms:
                j = i + 1
                percentages = []  # List to hold all percentages related to this fee
                search_limit = 1  # Limit the search to the next 5 words

                # Find all percentages related to this fee
                while j < len(tagged) and search_limit > 0:
                    # Move j to the next CD or JJ or '%'
                    while j < len(tagged) and tagged[j][1] not in ['CD', 'JJ', '%']:
                        j += 1
                        search_limit -= 1  # Decrement the search limit

                    # If j is a number and j+1 is a '%' symbol, save the percentage
                    if (
                        j < len(tagged)
                        and j + 1 < len(tagged)
                        and tagged[j + 1][0] == '%'
                        and tagged[j][0].replace('.', '').isdigit()
                    ):
                        percentages.append(tagged[j][0] + "%")
                        j += 2  # Move past the percentage symbol
                    else:
                        break

                if percentages:
                    fee_type = []
                    k = i - 1
                    while k >= 0 and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
                        fee_type.insert(0, tagged[k][0])
                        k -= 1
                    fee_name = ' '.join(fee_type) + ' ' + word.lower()
                    rewards[
                        fee_name.strip()
                    ] = percentages  # Save the list of percentages

        return rewards  # Return an empty dictionary if no suitable "reward" percentage is found

    def process_fee(self, text):
        keywords = ['fee', 'tax']
        words = word_tokenize(text)
        tagged = pos_tag(words)
        synonyms = self.get_synonyms(keywords)
        fees = {}
        for i, (word, tag) in enumerate(tagged):
            if word.lower() in synonyms:
                j = i + 1
                percentages = []  # List to hold all percentages related to this fee
                search_limit = 1  # Limit the search to the next 5 words

                # Find all percentages related to this fee
                while j < len(tagged) and search_limit > 0:
                    # Move j to the next CD or JJ or '%'
                    while j < len(tagged) and tagged[j][1] not in ['CD', 'JJ', '%']:
                        j += 1
                        search_limit -= 1  # Decrement the search limit

                    # If j is a number and j+1 is a '%' symbol, save the percentage
                    if (
                        j < len(tagged)
                        and j + 1 < len(tagged)
                        and tagged[j + 1][0] == '%'
                        and tagged[j][0].replace('.', '').isdigit()
                    ):
                        percentages.append(tagged[j][0] + "%")
                        j += 2  # Move past the percentage symbol
                    else:
                        break

                if percentages:
                    fee_type = []
                    k = i - 1
                    while k >= 0 and (tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
                        fee_type.insert(0, tagged[k][0])
                        k -= 1
                    fee_name = ' '.join(fee_type) + ' ' + word.lower()
                    fees[fee_name.strip()] = percentages  # Save the list of percentages
        return fees

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
                                supply_amount = amount.replace(',', '')
                            else:
                                supply_amount = amount
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


Based on the provided text, here are the numerical information related to the rate of reward or profit:

1. APR (Annual Percentage Rate): 2,920%
2. Dev Fee (Developer Fee): 3%
3. Marketing Fee: 2%
4. Referrals Earnings: 12% of the CRO (Croatian Kuna) deposited from anyone who uses your referral link.

Please note that the APR is an annual rate, and the actual rate of return may vary depending on the duration of the investment. Additionally, the referral earnings are based on the CRO deposited from users who sign up through your referral link, and the actual earnings may vary depending on the number of referrals and the amount deposited by each referral."""
extractor = FrontEndSpecsExtractor()

fees = extractor.process_reward1(test)
print(fees)
