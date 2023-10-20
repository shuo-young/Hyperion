from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import wordnet


# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')
class FrontEndSpecsExtractor:
    def __init__(self, text, keywords):
        self.text = text
        print(self.text)
        self.keywords = keywords
        self.words = word_tokenize(self.text)
        # 词性标注
        self.tagged = pos_tag(self.words)

    # analyze dapp frontend docs
    def process_rate(self):
        # 分词
        tagged = self.tagged
        synonyms = self.get_synonyms(self.keywords)
        fees = {}
        for i, (word, tag) in enumerate(tagged):
            if word.lower() in synonyms:
                j = i + 1
                percentages = []  # List to hold all percentages related to this fee

                # Find all percentages related to this fee
                while j < len(tagged):
                    # Move j to the next CD or JJ or '%'
                    while j < len(tagged) and tagged[j][1] not in ['CD', 'JJ', '%']:
                        j += 1

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

    def process_lock_time(self):
        tagged = self.tagged
        synonyms = self.get_synonyms(["lock", "locked", "locking"])
        lock_times = {}
        for i, (word, tag) in enumerate(self.tagged):
            if word.lower() in synonyms:
                j = i + 1
                time_periods = []

                # Find all time periods related to this lock
                while j < len(self.tagged):
                    # Check if the token is a number (either in digit or word form)
                    is_number = self.tagged[j][1] in ['CD', 'JJ'] or self.tagged[j][
                        0
                    ] in [
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
                        j < len(self.tagged)
                        and is_number
                        and (
                            self.tagged[j + 1][0].lower()
                            in ["year", "years", "month", "months", "day", "days"]
                        )
                    ):
                        time_periods.append(
                            self.tagged[j][0] + " " + self.tagged[j + 1][0]
                        )
                        j += 2
                    else:
                        j += 1  # Continue to the next token

                if time_periods:
                    lock_description = []
                    k = i - 1
                    while k >= 0 and (self.tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
                        lock_description.insert(0, self.tagged[k][0])
                        k -= 1
                    lock_name = ' '.join(lock_description) + ' ' + word.lower()
                    lock_times[lock_name.strip()] = time_periods

        return lock_times

    def process_supply(self):
        synonyms = self.get_synonyms(["supply"])
        supplies = {}
        for i, (word, tag) in enumerate(self.tagged):
            if word.lower() in synonyms:
                j = i + 1
                supply_amount = None

                # Find all amounts related to this supply keyword
                while j < len(self.tagged):
                    if self.tagged[j][1] == 'CD':
                        amount = self.tagged[j][0]
                        j += 1

                        # Handle cases where numbers are written like "275,000,000"
                        while (
                            j < len(self.tagged)
                            and self.tagged[j][0] in [',', '.']
                            and j + 1 < len(self.tagged)
                            and self.tagged[j + 1][1] == 'CD'
                        ):
                            amount += self.tagged[j][0] + self.tagged[j + 1][0]
                            j += 2

                        supply_amount = int(amount.replace(',', ''))
                        break
                    else:
                        j += 1

                if supply_amount:
                    supply_description = []
                    k = i - 1
                    while k >= 0 and (self.tagged[k][1] in ['NN', 'NNS', '&', 'JJ']):
                        supply_description.insert(0, self.tagged[k][0])
                        k -= 1
                    supply_name = ' '.join(supply_description) + ' ' + word.lower()
                    supplies[supply_name.strip()] = supply_amount

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


# extractor = FrontEndSpecsExtractor(text3, ["fee"])
# fees = extractor.process_supply()
# print(fees)
