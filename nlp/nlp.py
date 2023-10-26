from nltk.tokenize import word_tokenize
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
    def process_rate(self, text, keywords):
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
                    lock_times[lock_name.strip()] = time_periods

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
                    return {"Total Supply": supply_amount}

        return supplies

    def get_synonyms(self, keywords):
        # keywords = ['fee']
        synonyms = keywords[:]
        for keyword in keywords:
            for syn in wordnet.synsets(keyword):
                for lemma in syn.lemmas():
                    synonyms.append(lemma.name())

        # remove duplicated
        synonyms = list(set(synonyms))
        print(synonyms)
        return synonyms


text = """Hey! Based on the provided text, here are some important attributes and their values that can indicate the rate of reward or profit for users:

1. Daily Reward: The text mentions "3% Daily" which implies that users will receive a sell fee of 3%.

2. Annual Percentage Rate (APR): The text states "1,095% APR", which indicates the total return on investment (ROI) for the year, including the daily rewards.

3. Compounding: The text mentions "Compound Daily" which indicates that the daily rewards will be compounded, meaning the profit will increase exponentially over time.

However, there is no mention of a specific rate of return for each individual user, and the text does include a risk warning, indicating that investments in crypto and blockchain are high-risk and subject to market volatility.

Therefore, while there may be potential for profit, it is crucial to exercise caution and thorough research before investing."""

text1 = """Only users with locked Dynamic Liquidity (Liquidity Tokens) activate eligibility to receive RDNT emissions within the money market. 
$RDNT Liquidity mining emissions can be instantly claimed for the total amount on the condition that they are zapped into locked dLP tokens by pairing the claimed $RDNT with wstETH/BNB.
Alternatively, emissions may be vested for three months. Vesting RDNT may be claimed early for an exit penalty to receive 10-75% of rewards, decaying linearly during the three-month vesting period. 
This penalty fee is then distributed 90% to the Radiant DAO reserve, and the remaining 10% is sent to the Radiant Starfleet Treasury.
Locking dLP tokens is a one to twelve-month process and must be re-locked after maturity to continue receiving platform fees.
For a detailed breakdown of how dynamic liquidity provisioning functions, visit the dLP section of the Gitbook.
For a detailed breakdown of how Locking & Vesting work, visit the Manage Radiant section."""

text2 = """ Based on the text you provided, there is no explicit mention of liquidity lock time. However, there is a section that talks about liquidity security, which could be interpreted as a reference to the liquidity lock time. 

The section states, ""02 Total Security Liquidity locked up for a 5 years"" This could mean that the liquidity for the token is locked for a period of five years, which could help to stabilize the token's price and provide a sense of security for investors. However, without further information, it's difficult to confirm the exact duration of the liquidity lock time."""

text3 = """The text does not explicitly state the total amount or supply of the token. However, based on the information provided, we can infer that the total supply of PunkPanda tokens is 275,000,000, with 65,000,000 tokens allocated to the incubator (token pre-sale, marketing, airdrops, and PandaPal sharing rewards)."""

text4 = """Okey Dokey! Based on the provided text, here are the numerical information related to the rate of reward or profit:

* Daily Return: 8% APR
* Dev Fee: 5%

Here's the information in a key-value format as requested:

{
"Daily Return": 8,
"Dev Fee": 5
}"""

test = """Okey, I've gone through the text you provided, and I've extracted the numerical information related to the lock time as follows:

* Lock time: 3, 6, and 9 months

The text mentions that liquidity has been locked for 3, 6, and 9 months on Team Finance. The links provided in the text are:

* https://www.team.finance/view-coin/0xC84D8d03aA41EF941721A4D77b24bB44D7C7Ac55?name=Empire%20Capital%20Token&symbol=ECC
* https://bscscan.com/address/0xC84D8d03aA41EF941721A4D77b24bB44D7C7Ac55#code

Please note that the lock time information is based on the information provided in the text and may not be up-to-date or accurate."""
extractor = FrontEndSpecsExtractor()
fees = extractor.process_lock_time(test)
print(fees)
