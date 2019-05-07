#!/usr/bin/env python

from mbox import mbox
import decimal
import simplejson as json
import datetime
import platform
import logging
import gettext
import sys

# Logging Set Up
logger = logging.getLogger(__name__)


def exception_hook(logger, exc, val, tb):
    logger.error("An Unexpected Error: %s", val,
                 exc_info=(exc, val, tb))


# hook
sys.excepthook = lambda exc, val, tb: exception_hook(logger, exc, val, tb)


def upload_settings():
    try:
        with open('resources/settings.json', 'r') as doc:
            configs = json.load(doc)
        return configs
    except FileNotFoundError:
        with open('resources/settings_template.json', 'r') as doc:
            configs = json.load(doc)
        return configs


def get_language():
    # language paths
    en = gettext.translation('base', localedir='locales', languages=['en'])
    ru = gettext.translation('base', localedir='locales', languages=['ru'])
    uk = gettext.translation('base', localedir='locales', languages=['uk'])
    # check language
    lang_dict = {'en': en, 'ru': ru, 'uk': uk}
    language = upload_settings()['language']
    lang_dict[language].install()
    _ = lang_dict[language].gettext


if platform.system() == 'Darwin':  # if you're on a mac
    logger.info("You're on a Mac.")
    SIZE = 12
elif platform.system() == 'Windows':  # if you're on a windows
    logger.info("You're on a Windows PC.")
    SIZE = 12

D = decimal.Decimal
get_language()


def upload_ledger(directory=None):
    if directory is None:
        try:
            with open('resources/matrices.txt', 'r+', encoding='utf-8') as doc:
                ledg = json.load(doc)
                return ledg
        except FileNotFoundError:
            ledg = []
            return ledg
    else:
        with open(directory, "r+", encoding='utf-8') as doc:
            ledg = json.load(doc)
            return ledg


settings = upload_settings()
ledger = upload_ledger()


class BaseProgram:

    version = "0.0.5.2"  # SOFTWARE VERSION

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.version = BaseProgram.version

        self.settings = settings
        self.ledger = ledger  # [transaction, date, account, base, debit, credit, memo, payee]
        self.SIZE = SIZE

        self.fundnames = self.get_fundnames()
        # [transaction, date, account, base, debit, credit, memo, payee]
        if len(self.ledger) > 1:
            self.transaction = self.ledger[len(self.ledger)-1][0] + 1
        else:
            self.transaction = 1
        self.payee_names = self.settings['payee_names']

        self.cents = decimal.Decimal('.01')
        print('backend load successful')

    def get_funds(self):
        funds = []
        for category in self.settings['accounts']:
            for key in self.settings['accounts'][category]:
                funds.append(key)
        return funds

    def get_fundnames(self):
        names = []
        for category in self.settings['accounts']:
            for key in self.settings['accounts'][category]:
                names.append(self.settings['accounts'][category][key][0])
        return names

    def get_asset_fullname(self, number):
        name = '{} {}'.format(number, self.settings['accounts']['assets'][number][0])
        return name

    def get_liability_fullname(self, number):
        name = '{} {}'.format(number, self.settings['accounts']['liabilities'][number][0])
        return name

    def get_equity_fullname(self, number):
        name = '{} {}'.format(number, self.settings['accounts']['equities'][number][0])
        return name

    def get_revenue_fullname(self, number):
        name = '{} {}'.format(number, self.settings['accounts']['revenues'][number][0])
        return name

    def get_expense_fullname(self, number):
        name = '{} {}'.format(number, self.settings['accounts']['expenses'][number][0])
        return name

    def save(self):
        with open('resources/matrices.txt', 'w+', encoding='utf8') as doc:
            json.dump(self.ledger, doc, ensure_ascii=False)

    def add_fund(self, number, name, whole_percent=None, amount=None):
        source = []
        # checking to see if the number is already used
        if number.isnumeric():
            if number[0] == '1':
                if number not in self.settings['accounts']['assets']:
                    source = self.settings['accounts']['assets']
                else:
                    mbox(_('Error'), _('Error: Account number is already in use.'),
                         b1=_('Ok'), b2=None)
                    self.logger.warning("Error: Account number is already in use.")
            elif number[0] == '2':
                if number not in self.settings['accounts']['liabilities']:
                    source = self.settings['accounts']['liabilities']
                else:
                    mbox(_('Error'), _('Error: Account number is already in use.'),
                         b1=_('Ok'), b2=None)
                    self.logger.warning("Error: Account number is already in use.")
            elif number[0] == '3':
                if number not in self.settings['accounts']['equities']:
                    source = self.settings['accounts']['equities']
                else:
                    mbox(_('Error'), _('Error: Account number is already in use.'),
                         b1=_('Ok'), b2=None)
                    self.logger.warning("Error: Account number is already in use.")
            elif number[0] == '4':
                if number not in self.settings['accounts']['revenues']:
                    source = self.settings['accounts']['revenues']
                else:
                    mbox(_('Error'), _('Error: Account number is already in use.'),
                         b1=_('Ok'), b2=None)
                    self.logger.warning("Error: Account number is already in use.")
            elif number[0] == '6':
                if number not in self.settings['accounts']['expenses']:
                    source = self.settings['accounts']['expenses']
                else:
                    mbox(_('Error'), _('Error: Account number is already in use.'),
                         b1=_('Ok'), b2=None)
                    self.logger.warning("Error: Account number is already in use.")

            # percent & amount signifiers
            if whole_percent is not None:
                percent = round(float(whole_percent)/100, 2)
                source[number] = [name, percent, 0]
            elif amount is not None:
                source[number] = [name, 0, round(float(amount), 2)]
            else:
                source[number] = [name, 0, 0]
                
            self.logger.info("Added fund %s", number)

    def add_income(self, date, debit, credit, deb_amount, cred_amount, memo, payee=None):
        # if there is one debit fund and one credit fund
        if isinstance(debit, str) and isinstance(credit, str):
            # if the debit is a alternate currency with exrate
            if isinstance(deb_amount, tuple):
                self.add_to_alt_currency_records(debit, deb_amount[0], deb_amount[1])
                self.debit_ledger(self.transaction, date, debit, deb_amount[0],
                                  memo, deb_amount[1], payee)

                self.credit_ledger(self.transaction, date, credit, cred_amount, memo, None, payee)
            # if debit is base currency
            else:
                self.debit_ledger(self.transaction, date, debit, deb_amount, memo, None, payee)
                self.credit_ledger(self.transaction, date, credit, cred_amount, memo, None, payee)

        # if there is more than one debit fund
        elif isinstance(debit, list) and isinstance(credit, str):
            for x in range(0, len(debit)):
                # if debit is alternate currency with exrate
                if isinstance(deb_amount[x], tuple):
                    self.add_to_alt_currency_records(debit[x], deb_amount[x][0], deb_amount[x][1])
                    self.debit_ledger(self.transaction, date, debit[x],
                                      deb_amount[x][0], memo, deb_amount[x][1], payee)

                # if debit is base currency
                else:
                    self.debit_ledger(self.transaction, date, debit[x], deb_amount[x], memo, None, payee)

            self.credit_ledger(self.transaction, date, credit, cred_amount, memo, None, payee)
        # if there is one debit and multiple credits
        elif isinstance(debit, str) and isinstance(credit, list):
            # if debit is alternate currency with exrate
            if isinstance(deb_amount, tuple):
                self.add_to_alt_currency_records(debit, deb_amount[0], deb_amount[1])
                self.debit_ledger(self.transaction, date, debit, deb_amount[0], memo, deb_amount[1], payee)

            # if debit is base currency
            else:
                self.debit_ledger(self.transaction, date, debit, deb_amount, memo, None, payee)

            for x in range(0, len(credit)):
                self.credit_ledger(self.transaction, date, credit[x], cred_amount[x], memo, None, payee)

        elif isinstance(debit, list) and isinstance(credit, list):
            mbox(_('Inappropriate Transaction'),
                 _('Please separate this request into multiple transactions.'),
                 b1=_('Ok'), b2=None)
            self.logger.warning('Attempted to input multiple incomes.')

        self.transaction += 1

    def add_expense(self, date, debit, credit, deb_amount, cred_amount, memo, payee=None):
        # if there is one asset and one equity
        if isinstance(credit, str) and isinstance(debit, str):
            # if the asset is a alternate currency with exrate
            if isinstance(cred_amount, tuple):
                self.credit_ledger(self.transaction, date, credit,
                                   cred_amount[0], memo, cred_amount[1], payee)

                self.debit_ledger(self.transaction, date, debit, deb_amount, memo, None, payee)
            # if asset is base currency
            else:
                self.credit_ledger(self.transaction, date, credit, cred_amount, memo, None, payee)
                self.debit_ledger(self.transaction, date, debit, deb_amount, memo, None, payee)

        # if there is more than one asset
        elif isinstance(credit, list) and isinstance(debit, str):
            for x in range(0, len(credit)):
                # if asset is alternate currency with exrate
                if isinstance(cred_amount[x], tuple):
                    self.credit_ledger(self.transaction, date, credit[x],
                                       cred_amount[x][0], memo, cred_amount[x][1], payee)

                # if asset is base currency
                else:
                    self.credit_ledger(self.transaction, date, credit[x], cred_amount[x], memo, None, payee)

            self.debit_ledger(self.transaction, date, debit, deb_amount, memo, None, payee)

        # if there is one asset and multiple equities
        elif isinstance(credit, str) and isinstance(debit, list):
            # if asset is alternate currency with exrate
            if isinstance(cred_amount, tuple):
                self.credit_ledger(self.transaction, date, credit, cred_amount[0], memo, cred_amount[1], payee)

            # if asset is base currency
            else:
                self.credit_ledger(self.transaction, date, credit, cred_amount, memo, None, payee)

            for x in range(0, len(debit)):
                self.debit_ledger(self.transaction, date, debit[x], deb_amount[x], memo, None, payee)

        self.transaction += 1

    def add_transfer(self, date, from_fund, to_fund, from_amount, to_amount, memo):
        payee = None
        # if splitting one fund into two or more funds
        if isinstance(from_fund, str) and isinstance(to_fund, list):
            self.debit_ledger(self.transaction, date, from_fund, from_amount, memo, None, payee)

            for x in range(0, len(to_fund)):
                self.credit_ledger(self.transaction, date, to_fund[x], to_amount[x], memo, None, payee)
        # if gathering funds from a variety of funds into one
        elif isinstance(from_fund, list) and isinstance(to_fund, str):
            for x in range(0, len(from_fund)):
                self.debit_ledger(self.transaction, date, from_fund[x], from_amount[x], memo, None, payee)
            self.credit_ledger(self.transaction, date, to_fund, to_amount, memo, None, payee)
        # if there is one fund going into one fund
        else:
            self.debit_ledger(self.transaction, date, from_fund, from_amount, memo, None, payee)
            self.credit_ledger(self.transaction, date, to_fund, to_amount, memo, None, payee)

        self.transaction += 1

    def add_exchange(self, date, debit, credit, deb_amount, cred_amount, memo, payee=None):
        # if there is one debit fund and one credit fund (which there should always only be one
        if isinstance(debit, str) and isinstance(credit, str):
            # if the debit is a alternate currency with exrate
            if isinstance(deb_amount, tuple):
                self.credit_ledger(self.transaction, date, credit, cred_amount, memo, None, payee)
                self.add_to_alt_currency_records(debit, deb_amount[0], deb_amount[1])
                self.debit_ledger(self.transaction, date, debit, deb_amount[0], memo, deb_amount[1], payee)
            # if debit is base currency
            elif isinstance(cred_amount, tuple):
                self.credit_ledger(self.transaction, date, credit, cred_amount[0], memo, cred_amount[1], payee)
                self.debit_ledger(self.transaction, date, debit, deb_amount, memo, None, payee)
            else:
                self.debit_ledger(self.transaction, date, debit, deb_amount, memo, None, payee)
                self.credit_ledger(self.transaction, date, credit, cred_amount, memo, None, payee)
        # if there is more than one debit fund
        else:
            mbox(_('Error'), _('Exchanges are limited to two currencies.'),
                 b1=_('Ok'), b2=None)
            self.logger.warning("We limit an exchange between two currencies.")

        self.transaction += 1

    def add_offering(self, date, currencies, amount, memo):
        operating_funds = D('0.00')

        # calculate income from currencies & amounts entered
        if isinstance(currencies, list) and isinstance(amount, list):  # if there is more than one currency inputted
            for x in range(0, len(currencies)):
                if isinstance(amount[x], tuple):  # if alternate currencies
                    cur = amount[x][0]
                    exrate = amount[x][1]
                    self.add_to_alt_currency_records(currencies[x], cur, exrate)
                    self.debit_ledger(self.transaction, date, currencies[x], cur, memo, exrate, None)
                    operating_funds += (D(cur) * D(exrate)).quantize(self.cents, decimal.ROUND_HALF_UP)
                else:  # if main currency
                    cur = amount[x]
                    self.debit_ledger(self.transaction, date, currencies[x], cur, memo, None, None)
                    operating_funds += D(cur)
        else:  # if only one currency is inputted
            if isinstance(amount, tuple):  # if that currency is an alternate currency
                cur = amount[0]
                exrate = amount[1]
                self.add_to_alt_currency_records(currencies, cur, exrate)
                self.debit_ledger(self.transaction, date, currencies, cur, memo, exrate, None)
                operating_funds += (D(cur) * D(exrate)).quantize(self.cents, decimal.ROUND_HALF_UP)
            else:  # if that currency is base currency
                self.debit_ledger(self.transaction, date, currencies, amount, memo, None, None)
                operating_funds += D(amount)

        # calcuate and pay allocations
        if self.settings['allocations'][0] == 1:
            wef_dec = D(self.settings['allocations'][1]['WEF']) / D('100')
            wef = D(round(operating_funds * wef_dec)).quantize(D('1.00'), decimal.ROUND_HALF_UP)
            self.credit_ledger(self.transaction, date, '3010 WEF Allocations', wef, memo, None)
            dist_dec = D(self.settings['allocations'][1]['District']) / D('100')
            district = D(round(operating_funds * dist_dec)).quantize(D('1.00'), decimal.ROUND_HALF_UP)
            self.credit_ledger(self.transaction, date, '3011 District Allocations', district, memo, None)
            edu_dec = D(self.settings['allocations'][1]['Education']) / D('100')
            education = D(round(operating_funds * edu_dec)).quantize(D('1.00'), decimal.ROUND_HALF_UP)
            self.credit_ledger(self.transaction, date, '3012 Education Allocations', education, memo, None)

            operating_funds -= (wef + district + education)

        fund_amounts = self.get_fund_amounts()
        fund_percents = self.get_fund_percentages()

        # distribute funds per set amounts & percentages
        if len(fund_amounts) > 0:
            for x in fund_amounts:
                if operating_funds - D(x[1]) > 0:
                    self.credit_ledger(self.transaction, date, x[0], x[1], memo, None, None)
                    operating_funds -= D(x[1])

        if len(fund_percents) > 0:
            for x in fund_percents:
                percent = D(x[1]) / D('100')
                amt = (operating_funds * percent).quantize(self.cents, decimal.ROUND_HALF_UP)
                self.credit_ledger(self.transaction, date, x[0], amt, memo, None, None)

        self.transaction += 1

    # record to dictionary associated with alt. currency
    def add_to_alt_currency_records(self, fund, amount, exrate):
        # The funds for the alt. currency account are recorded in a dictionary
        # where {'string exrate':Decimal(value)}
        record = self.settings['accounts']['assets'][fund[:4]][1]
        string_rate = str(exrate)  # this may be redundant, but we want the key to be a numerical string
        if string_rate in record.keys():  # if the exrate already exists
            record[string_rate] = record[string_rate] + D(amount)
        else:
            record[string_rate] = D(amount)

    # checking for and removing cash amounts from alt. currency
    def subtract_from_alt_currency_records(self, fund, amount, exrate):
        # this information is understood in a dictionary where
        # {'string exrate':Decimal(value)}
        record = self.settings['accounts']['assets'][fund[:4]][1]
        string_rate = str(exrate)  # this may be redundant, but we want the key to be a numerical string
        if string_rate in record.keys():  # if the exrate exists
            if record[string_rate] - D(amount) < 0:
                name = fund[:4]
                question = mbox(_('Insufficient Funds'),
                                _('There is not enough in the {} account for that rate.'
                                  '\nWould you like to continue anyway?').format(name),
                                b1=_('Yes'), b2=_('No'))
                if question:
                    record[string_rate] = D(record[string_rate]) - D(amount)
                    return True
                else:
                    return False
            else:
                record[string_rate] = D(record[string_rate]) - D(amount)
                return True
        else:  # if the exrate does not exist
            question = mbox(_('Insufficient Funds'),
                            _('There is no exchange rate for {}.'
                              '\nWould you like to continue anyway?').format(string_rate),
                            b1=_('Yes'), b2=_('No'))
            if question:
                record[string_rate] = D(amount)
                return True
            else:
                return False

    def load_fund(self, fund_name):
        balance = D('0.00')
        tally = []
        # ledger_array = [trans#, date, account, base, debit, credit, exrate, memo, payee]
        # Fund_array = [trans#, date, amount, exrate, balance, memo, payee]
        if fund_name in self.settings['accounts']['assets']:
            for x in self.ledger:
                if fund_name in x[2]:
                    amount = (D(x[4]) + D((-x[5]))).quantize(self.cents, decimal.ROUND_HALF_UP)
                    if x[6] is not None:
                        exrate = D(x[6])
                    else:
                        exrate = x[6]
                    balance += amount
                    tally.append([x[0], x[1], amount, exrate, balance, x[7], x[8]])
        elif fund_name in self.settings['accounts']['liabilities']:
            for x in self.ledger:
                if fund_name in x[2]:
                    amount = (D((-x[4])) + D(x[5])).quantize(self.cents, decimal.ROUND_HALF_UP)
                    if x[6] is not None:
                        exrate = D(x[6])
                    else:
                        exrate = x[6]
                    balance += amount
                    tally.append([x[0], x[1], amount, exrate, balance, x[7], x[8]])
        elif fund_name in self.settings['accounts']['equities']:
            for x in self.ledger:
                if fund_name in x[2]:
                    amount = (D((-x[4])) + D(x[5])).quantize(self.cents, decimal.ROUND_HALF_UP)
                    if x[6] is not None:
                        exrate = D(x[6])
                    else:
                        exrate = x[6]
                    balance += amount
                    tally.append([x[0], x[1], amount, exrate, balance, x[7], x[8]])
        elif fund_name in self.settings['accounts']['revenues']:
            for x in self.ledger:
                if fund_name in x[2]:
                    amount = (D((-x[4])) + D(x[5])).quantize(self.cents, decimal.ROUND_HALF_UP)
                    if x[6] is not None:
                        exrate = D(x[6])
                    else:
                        exrate = x[6]
                    balance += amount
                    tally.append([x[0], x[1], amount, exrate, balance, x[7], x[8]])
        elif fund_name in self.settings['accounts']['expenses']:
            for x in self.ledger:
                if fund_name in x[2]:
                    amount = (D(x[4]) + D((-x[5]))).quantize(self.cents, decimal.ROUND_HALF_UP)
                    if x[6] is not None:
                        exrate = D(x[6])
                    else:
                        exrate = x[6]
                    balance += amount
                    tally.append([x[0], x[1], amount, exrate, balance, x[7], x[8]])
        else:
            mbox(_('Error'), _('Error: %s is not a fund number.') % fund_name,
                 b1=_('Ok'), b2=None)
            self.logger.warning("%s is not a fund number.", fund_name)
        return tally

    def calculate_balance_sheet(self):
        # assets
        asset = []
        for fund in self.settings['accounts']['assets']:
            if fund == '1010':
                try:
                    asset.append((self.get_asset_fullname(fund),
                                  self.load_fund(fund)[-1][4]))
                except IndexError:
                    asset.append((self.get_asset_fullname(fund), 0))
            else:
                try:
                    asset.append((self.get_asset_fullname(fund),
                                  (self.load_fund(fund)[-1][4], self.load_fund(fund)[-1][1])))
                except IndexError:
                    asset.append((self.get_asset_fullname(fund), (0, 0)))
        # liabilies
        liability = []
        for fund in self.settings['accounts']['liabilities']:
            try:
                liability.append((self.get_liability_fullname(fund),
                                  self.load_fund(fund)[-1][4]))
            except IndexError:
                liability.append((self.get_liability_fullname(fund), 0))
        # equities
        equity = []
        for fund in self.settings['accounts']['equities']:
            try:
                equity.append((self.get_equity_fullname(fund),
                               self.load_fund(fund)[-1][4]))
            except IndexError:
                equity.append((self.get_equity_fullname(fund), 0))
        # revenues
        revenue = []
        for fund in self.settings['accounts']['revenues']:
            try:
                revenue.append((self.get_revenue_fullname(fund),
                                self.load_fund(fund)[-1][4]))
            except IndexError:
                revenue.append((self.get_revenue_fullname(fund), 0))
        # expenses
        expense = []
        for fund in self.settings['accounts']['expenses']:
            try:
                expense.append((self.get_expense_fullname(fund),
                                self.load_fund(fund)[-1][4]))
            except IndexError:
                expense.append((self.get_expense_fullname(fund), 0))

        return [asset, liability, equity, revenue, expense]

    def get_fund_amounts(self):
        amount = []
        for category in self.settings['accounts']:
            if category != "assets":
                for key in self.settings['accounts'][category]:
                    if D(self.settings['accounts'][category][key][2]) > D('0'):
                        # append tuple (key + name, 0)
                        amount.append(('{} {}'.format(key, self.settings['accounts'][category][key][0]),
                                       self.settings['accounts'][category][key][2]))
        return amount

    def get_fund_percentages(self):
        percent = []
        for category in self.settings['accounts']:
            if category != "assets":
                for key in self.settings['accounts'][category]:
                    if D(self.settings['accounts'][category][key][1]) > D('0'):
                        # append tuple (key + name, 0)
                        percent.append(('{} {}'.format(key, self.settings['accounts'][category][key][0]),
                                        self.settings['accounts'][category][key][1]))
        return percent

    def debit_ledger(self, trans, date, account, amount, memo, exrate=None, payee=None):
        if exrate is not None:
            base = (D(amount) * D(exrate)).quantize(self.cents, decimal.ROUND_HALF_UP)
            exrate2 = D(exrate)
        else:
            base = D(amount).quantize(self.cents, decimal.ROUND_HALF_UP)
            exrate2 = None
        amt = D(amount).quantize(self.cents, decimal.ROUND_HALF_UP)
        self.ledger.append([trans, date, account, base, amt, 0, exrate2, memo, payee])

    def credit_ledger(self, trans, date, account, amount, memo, exrate=None, payee=None):
        if exrate is not None:
            base = (D(amount) * D(exrate)).quantize(self.cents, decimal.ROUND_HALF_UP)
            exrate2 = D(exrate)
        else:
            base = D(amount).quantize(self.cents, decimal.ROUND_HALF_UP)
            exrate2 = None
        amt = D(amount).quantize(self.cents, decimal.ROUND_HALF_UP)
        self.ledger.append([trans, date, account, base, 0, amt, exrate2, memo, payee])

    def save_to_file(self, ledg, configs):
        self.settings['payee_names'] = self.payee_names
        # save settings to file
        with open('resources/settings.json', 'w+', encoding='utf-8') as doc1:
            json.dump(configs, doc1, indent=2)

        # save ledger to file
        with open('resources/matrices.txt', 'w+', encoding='utf-8') as doc2:
            json.dump(ledg, doc2, indent=2, use_decimal=True)

    # figures out if there is enough funds and return true
    # get the latest fund and then subtract amount from it to see if it gets to 0
    def enough_funds(self, fund, amount):
        array = []
        if isinstance(fund, list):  # if there are multiple funds giving
            for x in range(len(fund)):
                if isinstance(amount[x], tuple):  # if the amount is an alt. currency (another function checks this)
                    pass
                else:  # If the amount isn't an alt. currency
                    try:  # try to get the latest amount
                        self.load_fund(fund[x][:4])[-1][4]
                    except IndexError:  # If there is nothing in the fund
                        array.append(0)
                    else:
                        a = D(amount[x]).quantize(self.cents, decimal.ROUND_HALF_UP)
                        if self.load_fund(fund[x][:4])[-1][4] - a >= D('0'):
                            array.append(1)
                        else:
                            array.append(0)
        else:  # if one fund giving
            if isinstance(amount, tuple):  # if the amount belongs to an alt. currency (another function checks this)
                return True
            else:  # if the amount is not an alt. currency
                try:  # try to get the lastest amount
                    self.load_fund(fund[:4])[-1][4]
                except IndexError:  # if there is nothing in the fund
                    array.append(0)
                else:
                    a = D(amount).quantize(self.cents, decimal.ROUND_HALF_UP)
                    if self.load_fund(fund[:4])[-1][4] - a >= D('0'):
                        array.append(1)
                    else:
                        array.append(0)
        if 0 in array:
            mbox(_('Insufficient Funds'),
                 _('There is not enough money in a fund to continue this transaction.'),
                 b1=_('Ok'), b2=None)
            return False
        else:
            return True


def check_date(date):
    if len(date) == 10:
        if date[6:].isdigit():
            year = int(date[6:])
        else:
            mbox(_('Date Error'), _('Year date needs to be four digits. (YYYY)'),
                 b1=_('Ok'), b2=None)
            logger.warning("Year needs to be in format YYYY")
            return False
        if date[3:5].isdigit():
            month = int(date[3:5])
        else:
            mbox(_('Date Error'), _('Month date needs to be two digits. (MM)'),
                 b1=_('Ok'), b2=None)
            logger.warning("Month needs to be in format MM")
            return False
        if date[:2].isdigit():
            day = int(date[:2])
        else:
            mbox(_('Date Error'), _('Day date needs to be two digits. (DD)'),
                 b1=_('Ok'), b2=None)
            logger.warning("Day needs to be in format DD")
            return False
        
        try:
            datetime.date(year, month, day)
            return True
        except ValueError:
            logger.exception("The date was not readable.")
            return False
    else:
        mbox(_('Date Error'), _('Please enter the date in format DD/MM/YYYY.'),
             b1=_('Ok'), b2=None)
        logger.warning("Please enter date in format DD/MM/YYYY")
        return False
