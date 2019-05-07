#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk, filedialog
from mbox import mbox
from backend import BaseProgram, check_date, exception_hook, upload_ledger, get_language
from buildreports import write_balance_sheet
from calculator import Calculator
import simplejson as json
import datetime
import decimal
import gettext
import logging
import logging.config
import os
import sys

get_language()


class UserInterface(BaseProgram):

    def __init__(self, master):
        super().__init__()

        # Logging
        self.logger = logging.getLogger(__name__)

        # PERMANENT VARIABLES
        self.FONT = self.settings['font']
        self.SIZE = 12
        self.primary = self.settings['bgcolor'][0]
        self.secondary = self.settings['bgcolor'][1]
        self.bg_row_color = 'gray93'

        # STYLING WIDGETS
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", background='white', highlightbackground=self.primary,
                        font=(self.FONT, self.SIZE))

        style.configure("Treeview.Heading", background="white", font=(self.FONT, self.SIZE), padding=2)
        style.configure("Treeview", font=(self.FONT, self.SIZE))

        style.configure("TLabel", font=(self.FONT, self.SIZE), background="white")
        style.configure("color.TLabel", background=self.primary)
        style.configure("header.TLabel", background=self.primary, font=(self.FONT, self.SIZE + 16))
        style.configure("header2.TLabel", background=self.primary, font=(self.FONT, self.SIZE + 8))

        style.configure("TFrame", background="white")
        style.configure("color.TFrame", background=self.primary)

        style.configure("TLabelframe", background="white")
        style.configure("TLabelframe.Label", font=(self.FONT, self.SIZE + 2), background="white")
        style.configure("color.TLabelframe", background=self.primary)
        style.configure("color.TLabelframe.Label", background=self.primary)

        style.configure("TCombobox", font=(self.FONT, self.SIZE),
                        selectbackground=self.secondary,
                        selectforeground='black',
                        fieldbackground="white")
        style.map("TCombobox", selectbackground=[("readonly", "white")])
        style.map("TCombobox", selectforeground=[("readonly", "black")])
        style.map("TCombobox", fieldbackground=[("readonly", "white")])

        style.configure("TCheckbutton", font=(self.FONT, self.SIZE + 2),
                        background=self.primary,
                        highlightcolor=self.secondary)
        style.map("TCheckbutton", background=[("active", self.primary),
                                              ("pressed", self.primary),
                                              ("selected", self.primary)])

        style.configure("TScrollbar", troughcolor=self.primary, arrowcolor=self.secondary,
                        background=self.primary)

        # SET VARIABLES
        # These variables are for formatting the ui for input windows
        self.credits = list()
        self.debits = list()
        self.debit_vars = list()
        self.credit_vars = list()
        self.input_debit_amounts = list()
        self.input_credit_amounts = list()
        self.win_window_open = False
        self.credit_var_check = tk.StringVar()
        self.payee_names = self.settings['payee_names']

        self.shadow_dict = dict(currency_dictionary())

        self.user = self.settings['user']['plebian']

        self.language_values = {'en': 'English',
                                'ru': u'Русский язык',
                                'uk': u'Українська мова'}
        self.account_keys = []
        for key in self.settings['accounts']:
            self.account_keys.append(key)

        self.fund_definitions = {'assets': _('Resources owned by the church, usually cash or bank accounts. '
                                             'For example: cash, land, building, equipment'),
                                 'liabilities': _('Debts owed by the church like loans. '
                                                  'For example: loans or mortgages.'),
                                 'equities': _('Funds available to meet needs of the church.'),
                                 'revenues': _('Income to the church. Revenue minus expenses equal equity.'),
                                 'expenses': _('Payments made by the church. Revenue minus expenses equal equity.')}

        # Master frame
        self.master = master
        self.master.config(bg=self.primary, padx=5, pady=5)

        # -- Configure Master Frame -- #
        # Gets the requested values of the height and width.
        self.window_width = 1000
        self.window_height = 500

        # Gets both half the screen width/height and window width/height
        self.positionRight = int(self.master.winfo_screenwidth() / 2 - self.window_width / 2)
        self.positionDown = int(self.master.winfo_screenheight() / 2 - self.window_height / 2)

        # Positions the window in the center of the page.
        self.master.geometry("+{}+{}".format(self.positionRight, self.positionDown))

        self.master.title(_("Church Financial Accountability Program {}")
                          .format(BaseProgram.version))
        self.master.resizable(False, False)

        # Everything Started Up
        self.logger.info("Program Started & Ready")

        if not self.settings["Church Name"]:
            self.check_first_time(self.master)
        else:
            self.start_ui(self.master)

    # Check to see if the program was opened the first time.
    # Open window with initial settings setup when starting a command for the first time.
    def check_first_time(self, frame):
        frame = ttk.Frame(self.master, style="color.TFrame")
        frame.grid(column=0, row=0, padx=10, pady=10)

        # Header & Text
        header = ttk.Label(frame, text="Welcome!", style="header2.TLabel")
        header.grid(column=0, row=0, columnspan=2)
        text = ttk.Label(frame, text="To start a new profile, please select your "
                                     "language, primary currency and church/organization's name.",
                         wrap="5in", justify='center', style="color.TLabel")
        text.grid(column=0, row=1, columnspan=2, sticky='we')

        # Language Setup
        lang_text = ttk.Label(frame, text="Language:", style="color.TLabel")
        lang_text.grid(column=0, row=2, sticky='w', pady=5)

        langs = [self.language_values[x] for x in self.language_values]
        lang_cb = ttk.Combobox(frame, values=langs, exportselection=0, state='readonly')
        lang_cb.set(self.language_values[self.settings['language']])
        lang_cb.option_add("*TCombobox*Listbox.selectBackground", self.secondary)
        lang_cb.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        lang_cb.grid(column=1, row=2, sticky='we')

        # Currency Setup
        cur_text = ttk.Label(frame, text="Primary currency:", style="color.TLabel")
        cur_text.grid(column=0, row=3, sticky='w', pady=5)

        cur_values = []
        for s in self.shadow_dict:
            cur_values.append('{} ({})'.format(s, self.shadow_dict[s]))

        cur_cb = ttk.Combobox(frame, state="readonly", exportselection=0, values=cur_values, width=26)
        cur_cb.option_add("*TCombobox*Listbox.selectBackground", self.secondary)
        cur_cb.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        cur_cb.grid(column=1, row=3, sticky='we')

        name_text = ttk.Label(frame, text="Church/Organization's name:", wrap=120, style="color.TLabel")
        name_text.grid(column=0, row=4, sticky='w')

        name = ttk.Entry(frame, font=(self.FONT, self.SIZE), width=30)
        name.grid(column=1, row=4, sticky='we')

        # Buttons
        button_frame = ttk.Frame(frame, style="color.TFrame")
        button_frame.grid(column=0, row=5, columnspan=2, sticky='we', pady=5)

        enter_button = ttk.Button(button_frame, text="Enter",
                                  command=lambda: self.submit_first_time_prompts(frame, lang_cb.get(),
                                                                                 cur_cb.get(), name.get()))
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.master.destroy)

        cancel_button.pack(side='right', padx=5)
        enter_button.pack(side='right', padx=5)

    # enter button command for "check first time" frame
    def submit_first_time_prompts(self, frame, language, currency, name):
        if not name:
            print("Please enter your church's/organization's name.")
            return
        else:
            for lang in self.language_values:
                if self.language_values[lang] == language:
                    self.settings['language'] = lang
                    self.save_all_to_file()
                    get_language()
                    self.page_title = ""
            self.settings["Church Name"] = name
            self.fund_creation(frame, "assets", "1010", "Cash " + currency[-4:-1],
                               "The amount of cash on hand.", currency)
            self.start_ui(self.master)

    # Create all UI for normal program development
    def start_ui(self, frame):
        if frame.winfo_children():
            for child in frame.winfo_children():
                child.destroy()

        #  -- Other frames -- #
        # Create Menubar
        self.setup_menubar(frame)
        self.setup_menubar(frame)

        # Directory Frame
        self.menu_directory_frame = ttk.Frame(frame, style="color.TFrame")
        self.menu_directory_frame.grid(column=0, row=3, sticky="NSWE")

        # Fund Page frame
        self.page = ttk.Frame(frame, width=800, relief='ridge', borderwidth=2,
                              style="color.TFrame")
        self.page.grid(column=1, row=3, rowspan=10, padx=2, pady=2, columnspan=3)

        self.church_name = ttk.Label(frame, text=self.settings['Church Name'], style="header2.TLabel",
                                     wraplength="2.5i")

        self.church_name.grid(column=0, row=0, sticky='nw')

        # Create Transaction Button frame & buttons
        self.transaction_buttons_menu = ttk.Frame(frame, style="color.TFrame")
        self.transaction_buttons_menu.grid(column=1, row=0, sticky='nwe')

        self.offering_button = ttk.Button(self.transaction_buttons_menu, text=_('Offering'),
                                          command=lambda: self.set_offering_window())
        self.income_button = ttk.Button(self.transaction_buttons_menu, text=_('Income'),
                                        command=lambda: self.setup_transaction_window('income'))
        self.expense_button = ttk.Button(self.transaction_buttons_menu, text=_('Expense'),
                                         command=lambda: self.setup_transaction_window('expense'))
        self.transfer_button = ttk.Button(self.transaction_buttons_menu, text=_('Transfer'),
                                          command=lambda: self.setup_transaction_window('transfer'))
        self.exchange_button = ttk.Button(self.transaction_buttons_menu, text=_('Exchange'),
                                          command=lambda: self.setup_transaction_window('exchange'))

        self.offering_button.pack(side='left', fill='both', expand='yes')
        self.income_button.pack(side='left', fill='both', expand='yes')
        self.expense_button.pack(side='left', fill='both', expand='yes')
        self.transfer_button.pack(side='left', fill='both', expand='yes')
        self.exchange_button.pack(side='left', fill='both', expand='yes')

        # --- populate self.page ---
        # create title
        self.page_title = ttk.Label(self.page, text="text", style="header.TLabel")
        self.page_title.grid(column=0, row=0, sticky="w", pady=5, padx=5)

        # Create Search Widget frame & widgets
        search_frame = ttk.Frame(self.page, style="color.TFrame")
        search_frame.grid(column=9, row=0, sticky='se', columnspan=2)

        search_label = ttk.Label(search_frame, text=_('Search'), style="color.TLabel")
        search_label.pack(side='left')

        self._toSearch = tk.StringVar()
        search_tree_entry = ttk.Entry(search_frame, width=20, textvariable=self._toSearch, font=(self.FONT, self.SIZE))
        search_tree_entry.pack(side='left')

        search_tree_entry.config(state='disabled')  # search ability not yet usable
        self._toSearch.trace_variable('w', lambda x, y, z: self.search_treeview())

        # Create Label for Right Clicking Notice
        self.page_label = ttk.Label(self.page, text=_("*Right click to get to the bottom."),
                                    style="color.TLabel")

        self.page_label.grid(column=0, row=2, sticky='w', columnspan=2)

        self.save_label = ttk.Label(frame, text="Last Saved:           ", style="color.TLabel")
        self.save_label.grid(column=3, row=2, sticky='e')

        self.populate_fund_menu_directory(self.menu_directory_frame)

        self.settings_checker = self.settings

        self.my_funds = self.get_funds()

        self.master.update_idletasks()
        print("frontend load successful")

    # Creates the menu options located at the top of the screen (Mac)
    # or top of the window (Windows)
    def setup_menubar(self, frame):
        self.menubar = tk.Menu(frame, font=(self.FONT, 12))
        frame.config(menu=self.menubar)

        self.file_menu = tk.Menu(self.menubar)
        self.file_menu.add_command(label=_('Save'),
                                   command=self.save_data)
        self.file_menu.add_command(label=_('Print'), state='disable',
                                   command=placeholder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=_('Import Ledger'), state='disable',
                                   command=import_ledger_file)
        self.file_menu.add_command(label=_('Export Ledger'), state='disable',
                                   command=placeholder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=_('Exit'),
                                   command=self.on_exit)
        self.menubar.add_cascade(label=_('File'), menu=self.file_menu)

        self.edit_menu = tk.Menu(self.menubar)
        self.edit_menu.add_command(label=_('Add/Remove Funds'),
                                   command=lambda: self.set_settings_window("fund_accounts"))
        self.edit_menu.add_command(label=_('Tithes & Offerings Settings'),
                                   command=lambda: self.set_settings_window("offering"))
        self.edit_menu.add_command(label=_("Edit Church Name"),
                                   command=lambda: self.set_settings_window("church_name"))
        self.edit_menu.add_command(label=_("Change Language"),
                                   command=lambda: self.set_settings_window("language"))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label=_('Clear Cache of Payee Names'),
                                   command=self.clear_name_prompts)
        self.menubar.add_cascade(label=_("Edit"), menu=self.edit_menu)

        self.trans_menu = tk.Menu(self.menubar)
        self.trans_menu.add_command(label=_('Add Offering'),
                                    command=self.set_offering_window)
        self.trans_menu.add_separator()
        self.trans_menu.add_command(label=_('Add Income'),
                                    command=lambda: self.setup_transaction_window('income'))
        self.trans_menu.add_command(label=_('Add Expense'),
                                    command=lambda: self.setup_transaction_window('expense'))
        self.trans_menu.add_command(label=_('Add Transfer'),
                                    command=lambda: self.setup_transaction_window('transfer'))
        self.trans_menu.add_command(label=_('Add Exchange'),
                                    command=lambda: self.setup_transaction_window('exchange'))
        self.menubar.add_cascade(label=_('Transactions'), menu=self.trans_menu)

        self.report_menu = tk.Menu(self.menubar)
        self.report_menu.add_command(label=_('Generate a Report'), command=placeholder, state="disable")
        self.report_menu.add_command(label=_('Generate Balance Sheet'), command=self.generate_balance_report)
        self.menubar.add_cascade(label=_('Reports'), menu=self.report_menu)

        self.helpmenu = tk.Menu(self.menubar)
        self.helpmenu.add_command(label=_('Calculator'),
                                  command=lambda: Calculator(tk.Toplevel(), self.primary).start_up)
        self.helpmenu.add_command(label=_('About CFAP'), command=about)
        self.menubar.add_cascade(label=_('Help'), menu=self.helpmenu)

        # Disabled menu items (because they are placeholders at the moment)
        self.report_menu.entryconfig(0, state='disabled')

    # Populates the 'Menu' of Frames located to the left of the window
    def populate_fund_menu_directory(self, frame):
        if frame.winfo_children():
            for child in frame.winfo_children():
                child.destroy()

        self.directory_label = ttk.Label(frame, text=_("MENU"), style="header2.TLabel")
        self.directory_label.grid(column=0, row=0, columnspan=2)

        # Button widgets
        gl_button = ttk.Button(frame, text=_("General Ledger"), style="color.TButton",
                               command=lambda: self.fund_page(self.page, _("General Ledger"), self.ledger))
        gl_button.grid(column=0, row=1, sticky='nswe')

        directory_buttons = list()
        funds = self.get_funds()
        fundnames = self.get_fundnames()
        for x in funds:
            i = funds.index(x)
            directory_buttons.append(ttk.Button(frame, text=fundnames[funds.index(x)],
                                                style="color.TButton",
                                                command=lambda x=x: self.fund_page(self.page,
                                                                                   fundnames[funds.index(x)],
                                                                                   self.load_fund(x))))
            directory_buttons[-1].grid(column=0, row=i+2, sticky='nswe')

        self.populate_directory_amounts()

        self.fund_page(self.page, _("General Ledger"), self.ledger)

    # This creates information that is displayed for each fund
    #  Displaying as Follows:
    #  General Ledger - Trans. #, Date, Account, Base, Debit, Credit, Exchange Rate, Memo, Payee
    #  Alt. Currency - Trans. #, Date, Amount, Exchange Rate, Loc. Balance, Base Value, Base Balance, Memo, Name
    #  Other fund - Trans. #, Date, Amount, Balance, Memo, Payee
    def fund_page(self, frame, title, data):
        self.tree = ttk.Treeview(frame, height=20)
        self.tree.grid(column=0, row=1, sticky="NSEW", columnspan=10)

        self.scrollbar = ttk.Scrollbar(frame, command=self.tree.yview)
        self.scrollbar.grid(column=11, row=1, sticky='NSE')
        self.tree.config(yscrollcommand=self.scrollbar.set)

        alternate_currencies = []
        for x in self.settings['accounts']['assets']:
            if x != '1010':
                alternate_currencies.append(self.settings['accounts']['assets'][x][0])

        # ---- if GENERAL LEDGER is selected ---- #
        if title == _("General Ledger"):
            self.page_title.config(text=title)

            self.tree.delete(*self.tree.get_children())
            self.tree.config(columns=('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'))
            self.tree.heading('#0', text=_('#'), command=lambda: self.fund_page(frame, title, data))
            self.tree.heading('#1', text=_('Date'), command=lambda: self.sort_date_column(self.tree, '#1', False))
            self.tree.heading('#2', text=_('Account'), command=lambda: self.sort_column(self.tree, '#2', False))
            self.tree.heading('#3', text=_('Base'), command=lambda: self.sort_column(self.tree, '#3', False))
            self.tree.heading('#4', text=_('Debit'), command=lambda: self.sort_column(self.tree, '#4', False))
            self.tree.heading('#5', text=_('Credit'), command=lambda: self.sort_column(self.tree, '#5', False))
            self.tree.heading('#6', text=_('Ex-Rate'), command=lambda: self.sort_column(self.tree, '#6', False))
            self.tree.heading('#7', text=_('Memo'), command=lambda: self.sort_column(self.tree, '#7', False))
            self.tree.heading('#8', text=_('Payee'), command=lambda: self.sort_column(self.tree, '#8', False))
            self.tree.column('#0', stretch=False, width=50, anchor='w')
            self.tree.column('#1', stretch=False, width=90, anchor='w')
            self.tree.column('#2', stretch=False, width=110, anchor='e')
            self.tree.column('#3', stretch=False, width=85, anchor='e')
            self.tree.column('#4', stretch=False, width=95, anchor='e')
            self.tree.column('#5', stretch=False, width=95, anchor='e')
            self.tree.column('#6', stretch=False, width=45, anchor='e')
            self.tree.column('#7', stretch=False, width=150, anchor='w')
            self.tree.column('#8', stretch=False, width=90, anchor='w')
            for entry in data:
                a = list()
                a.append(entry[0])  # add transaction date because
                for x in entry[1:]:  # don't change transaction number
                    if x == D('0'):
                        a.append('')
                    elif x is None:
                        a.append('')
                    else:
                        a.append(x)
                if len(self.tree.get_children('')) % 2 == 0:
                    self.tree.insert('', 'end', text=a[0], tags='evenrow',
                                     values=(a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))
                else:
                    self.tree.insert('', 'end', text=a[0], tags='oddrow',
                                     values=(a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))

        # ---- if an ALTERNATE CURRENCY ---- #
        elif title in alternate_currencies:
            self.page_title.config(text=title)

            self.tree.delete(*self.tree.get_children())
            self.tree.config(columns=('A', 'B', 'C', 'D', 'E', 'F', 'G', 'I'))
            self.tree.heading('#0', text=_('#'), command=lambda: self.fund_page(frame, title, data))
            self.tree.heading('#1', text=_('Date'), command=lambda: self.sort_date_column(self.tree, '#1', False))
            self.tree.heading('#2', text=_('Amount'), command=lambda: self.sort_column(self.tree, '#2', False))
            self.tree.heading('#3', text=_('Exchange'), command=lambda: self.sort_column(self.tree, '#3', False))
            self.tree.heading('#4', text=_('Balance'), command=lambda: self.sort_column(self.tree, '#4', False))
            self.tree.heading('#5', text=_('Base'), command=lambda: self.sort_column(self.tree, '#5', False))
            self.tree.heading('#6', text=_('Base Balance'), command=lambda: self.sort_column(self.tree, '#6', False))
            self.tree.heading('#7', text=_('Memo'), command=lambda: self.sort_column(self.tree, '#7', False))
            self.tree.heading('#8', text=_('Payee'), command=lambda: self.sort_column(self.tree, '#8', False))
            self.tree.column('#0', stretch=False, width=50, anchor='w')
            self.tree.column('#1', stretch=False, width=90, anchor='w')
            self.tree.column('#2', stretch=False, width=100, anchor='e')
            self.tree.column('#3', stretch=False, width=50, anchor='e')
            self.tree.column('#4', stretch=False, width=100, anchor='e')
            self.tree.column('#5', stretch=False, width=100, anchor='e')
            self.tree.column('#6', stretch=False, width=100, anchor='e')
            self.tree.column('#7', stretch=False, width=125, anchor='w')
            self.tree.column('#8', stretch=False, width=95, anchor='w')

            base_amount = D('0.00')
            for entry in data:
                a = list()
                a.append(entry[0])  # add transaction number because we don't want to change it at all
                for x in entry[1:]:  # any 0s or None statements should show up blank
                    if x != entry[4]:
                        if x == D('0'):
                            a.append('')
                        elif x is None:
                            a.append('')
                        else:
                            a.append(x)
                    else:  # don't change 'amount'
                        a.append(x)
                amount = (a[2] * a[3]).quantize(self.cents, decimal.ROUND_HALF_UP)
                base_amount += amount
                if len(self.tree.get_children('')) % 2 == 0:
                    self.tree.insert('', 'end', text=a[0], tags='evenrow',
                                     values=(a[1], a[2], a[3], a[4], amount, base_amount, a[5], a[6]))
                else:
                    self.tree.insert('', 'end', text=a[0], tags='oddrow',
                                     values=(a[1], a[2], a[3], a[4], amount, base_amount, a[5], a[6]))
        #
        # ---- all OTHER FUNDS ----- #
        #
        else:
            self.page_title.config(text=title)

            self.tree.delete(*self.tree.get_children())
            self.tree.config(columns=('A', 'B', 'C', 'D', 'E'))
            self.tree.heading('#0', text=_('#'), command=lambda: self.fund_page(frame, title, data))
            self.tree.heading('#1', text=_('Date'), command=lambda: self.sort_date_column(self.tree, '#1', False))
            self.tree.heading('#2', text=_('Amount'), command=lambda: self.sort_column(self.tree, '#2', False))
            self.tree.heading('#3', text=_('Balance'), command=lambda: self.sort_column(self.tree, '#4', False))
            self.tree.heading('#4', text=_('Memo'), command=lambda: self.sort_column(self.tree, '#5', False))
            self.tree.heading('#5', text=_('Payee'), command=lambda: self.sort_column(self.tree, '#6', False))
            self.tree.column('#0', stretch=False, width=60, anchor='w')
            self.tree.column('#1', stretch=False, width=95, anchor='w')
            self.tree.column('#2', stretch=False, width=120, anchor='e')
            self.tree.column('#3', stretch=False, width=120, anchor='e')
            self.tree.column('#4', stretch=False, width=245, anchor='w')
            self.tree.column('#5', stretch=False, width=170, anchor='w')
            for entry in data:
                a = list()
                a.append(entry[0])  # add transaction number because we
                for x in entry[1:]:  # don't change transaction number
                    if x == D('0'):
                        a.append('')
                    elif x is None:
                        a.append('')
                    else:
                        a.append(x)
                if a[4] == '':
                    a[4] = D('0').quantize(self.cents, decimal.ROUND_HALF_UP)
                if len(self.tree.get_children('')) % 2 == 0:
                    self.tree.insert('', 'end', text=a[0], tags='evenrow',
                                     values=(a[1], a[2], a[4], a[5], a[6]))
                else:
                    self.tree.insert('', 'end', text=a[0], tags='oddrow',
                                     values=(a[1], a[2], a[4], a[5], a[6]))

        self.tree.tag_configure('oddrow', background=self.secondary)

        self.tree.bind("<Double-1>", lambda e: self._on_doubleclick(e))
        self.tree.bind("<Button-2>", lambda e: self._on_right_click(e))

    # Populates the widgets for the window to give an offering
    def set_offering_window(self):
        if self.win_window_open is True:
            mbox(_('Window Open'),
                 _('You need to close a transaction window before beginning another.'),
                 b1=_('Ok'), b2=None)
            return
        else:
            self.win_window_open = True
            self.win = tk.Toplevel()
            self.win.protocol('WM_DELETE_WINDOW', self.close_window)
            # self.win.attributes('-topmost', 'true')

        # Title
        self.win_title = ttk.Label(self.win, text=_('Input Offering'), style="header.TLabel")
        self.win_title.grid(column=0, row=0, columnspan=3, sticky='we', pady=(0, 10))
        self.win.configure(background=self.primary, padx=5, pady=5)

        # Date label & input
        self.date_label = ttk.Label(self.win, text=_('Date (DD/MM/YYYY)'), justify='left', style="color.TLabel")
        todaysdate = datetime.datetime.now().strftime('%d/%m/%Y')
        self.date_input = ttk.Combobox(self.win, values=todaysdate, width=10)
        self.date_input.option_add("*TCombobox*Listbox.selectBackground", self.secondary)
        self.date_input.option_add("*TCombobox*Listbox.selectForeground", "#000000")

        self.date_label.grid(column=0, row=1, sticky='w')
        self.date_input.grid(column=1, row=1, sticky='e')

        # Memo
        self.memo_label = ttk.Label(self.win, text=_('Description/Memo'), justify='left', style="color.TLabel")
        self.memo_input = ttk.Entry(self.win, width=45, font=(self.FONT, self.SIZE))

        self.memo_label.grid(column=0, row=4, columnspan=3, sticky='w')
        self.memo_input.grid(column=0, row=5, columnspan=3, sticky='we')

        # Debit Frame ----------------------------
        self.debit_frame = ttk.LabelFrame(self.win, text=_('Debit'), style="color.TLabelframe")
        self.debit_frame.grid(column=0, row=6, sticky='we', columnspan=3, pady=5)

        # Clear Lists
        debit_button = []
        self.input_debit_amounts = []
        self.debits = []
        self.debit_vars = []

        for funds in self.settings['accounts']['assets']:  # creating a list of assets
            self.debits.append("{} {}".format(funds, self.settings['accounts']['assets'][funds][0]))

        self.create_frame_buttons(self.debit_frame, debit_button, self.debits,
                                  self.debit_vars, self.input_debit_amounts)

        # Enter and Cancel Buttons
        button_frame = ttk.Frame(self.win, style="color.TFrame")
        button_frame.grid(column=0, row=8, columnspan=3, pady=5)
        self.enter_button = ttk.Button(button_frame, text=_('ENTER'),
                                       command=lambda: self.verify_transaction('offering'))
        self.cancel_button = ttk.Button(button_frame, text=_('CANCEL'),
                                        command=lambda: self.close_window(self.win))

        self.enter_button.pack(side='left')
        self.cancel_button.pack(side='left')

        self.date_input.focus()

    # Populates the widgets to make a general transaction
    def setup_transaction_window(self, transaction):
        if self.win_window_open is True:
            mbox(_('Window Open'),
                 _('You need to close a transaction window before beginning another.'),
                 b1=_('Ok'), b2=None)
            return
        else:
            self.win_window_open = True
            self.win = tk.Toplevel()
            self.win.protocol('WM_DELETE_WINDOW', self.close_window)
            # self.win.attributes('-topmost', 'true')

        # Title
        self.win_title = ttk.Label(self.win, text=_('Input {}').format(transaction.title()), style='header.TLabel')
        self.win_title.grid(column=0, row=0, columnspan=2, sticky='we', pady=(0, 10))
        self.win.configure(background=self.primary, padx=5, pady=5)

        # Date label & input
        self.date_label = ttk.Label(self.win, text=_('Date (DD/MM/YYYY)'), justify='left', style="color.TLabel")
        today = datetime.datetime.now().strftime('%d/%m/%Y')
        self.date_input = ttk.Combobox(self.win, values=today, width=15, font=(self.FONT, self.SIZE))
        self.date_input.option_add("*TCombobox*Listbox.selectBackground", self.secondary)
        self.date_input.option_add("*TCombobox*Listbox.selectForeground", "#000000")

        self.date_label.grid(column=0, row=1, sticky='w')
        self.date_input.grid(column=1, row=1, sticky='e')

        # Payee label & input
        self.payee_label = ttk.Label(self.win, text=_('Name/Payee'), justify='left', style="color.TLabel")
        self.payee_input = ttk.Combobox(self.win, values=self.payee_names, width=30, font=(self.FONT, self.SIZE))
        self.payee_input.option_add("*TCombobox*Listbox.selectBackground", self.secondary)
        self.payee_input.option_add("*TCombobox*Listbox.selectForeground", "#000000")

        self.payee_label.grid(column=0, row=2, columnspan=3, sticky='w')
        self.payee_input.grid(column=0, row=3, columnspan=3, sticky='we')

        # Memo label & input
        self.memo_label = ttk.Label(self.win, text=_('Description/Memo'), justify='left', style="color.TLabel")
        self.memo_input = ttk.Entry(self.win, width=45, font=(self.FONT, self.SIZE))

        self.memo_label.grid(column=0, row=4, columnspan=3, sticky='w')
        self.memo_input.grid(column=0, row=5, columnspan=3, sticky='we')

        # ------- Debit Frame ----------------------------
        self.debit_frame = ttk.LabelFrame(self.win, text=_('Debit'), style="color.TLabelframe")
        self.debit_frame.grid(column=0, row=6, sticky='we', columnspan=3, pady=2)

        # Clear Lists
        debit_button = []  # list of button names
        self.input_debit_amounts = []  # list of debit amounts
        self.debits = []  # list of funds as debits
        self.debit_vars = []  # list of variables in credits

        if transaction == 'income':
            self.debit_frame.configure(text=_('Debit'))
            for funds in self.settings['accounts']['assets']:
                self.debits.append(self.get_asset_fullname(funds))
        elif transaction == 'expense':
            self.debit_frame.configure(text=_('Debit'))
            for funds in self.settings['accounts']['liabilities']:
                self.debits.append(self.get_liability_fullname(funds))
            for funds in self.settings['accounts']['equities']:
                self.debits.append(self.get_equity_fullname(funds))
            for funds in self.settings['accounts']['revenues']:
                self.debits.append(self.get_revenue_fullname(funds))
        elif transaction == 'transfer':
            self.debit_frame.configure(text=_('Debit (TAKING FROM)'))
            for funds in self.settings['accounts']['liabilities']:
                self.debits.append(self.get_liability_fullname(funds))
            for funds in self.settings['accounts']['equities']:
                self.debits.append(self.get_equity_fullname(funds))
            for funds in self.settings['accounts']['revenues']:
                self.debits.append(self.get_revenue_fullname(funds))
        elif transaction == 'exchange':
            self.debit_frame.configure(text=_('Debit (GOING TO)'))
            for funds in self.settings['accounts']['assets']:
                self.debits.append(self.get_asset_fullname(funds))

        self.create_frame_buttons(self.debit_frame, debit_button, self.debits,
                                  self.debit_vars, self.input_debit_amounts)

        # ------- Credit Frame -----------------------------
        self.credit_frame = ttk.LabelFrame(self.win, text=_('Credit'), style="color.TLabelframe")
        self.credit_frame.grid(column=0, row=7, sticky='we', columnspan=3, pady=2)

        # Clear Lists
        credit_button = []  # list of button names
        self.input_credit_amounts = []  # list of credit amounts
        self.credits = []  # list of funds as credit
        self.credit_vars = []  # list of variables in credits

        if transaction == 'income':
            self.credit_frame.configure(text=_('Credit'))
            for funds in self.settings['accounts']['liabilities']:
                self.credits.append(self.get_liability_fullname(funds))
            for funds in self.settings['accounts']['equities']:
                self.credits.append(self.get_equity_fullname(funds))
            for funds in self.settings['accounts']['revenues']:
                self.credits.append(self.get_revenue_fullname(funds))
        elif transaction == 'expense':
            self.credit_frame.configure(text=_('Credit'))
            for funds in self.settings['accounts']['assets']:
                self.credits.append(self.get_asset_fullname(funds))
        elif transaction == 'transfer':
            self.credit_frame.configure(text=_('Credit (GOING TO)'))
            for funds in self.settings['accounts']['liabilities']:
                self.credits.append(self.get_liability_fullname(funds))
            for funds in self.settings['accounts']['equities']:
                self.credits.append(self.get_equity_fullname(funds))
            for funds in self.settings['accounts']['revenues']:
                self.credits.append(self.get_revenue_fullname(funds))
        elif transaction == 'exchange':
            self.credit_frame.configure(text=_('Credit (TAKING FROM)'))
            for funds in self.settings['accounts']['assets']:
                self.credits.append(self.get_asset_fullname(funds))

        self.create_frame_buttons(self.credit_frame, credit_button, self.credits,
                                  self.credit_vars, self.input_credit_amounts)

        # Enter and Cancel Buttons
        button_frame = tk.Frame(self.win)
        button_frame.grid(column=0, row=8, columnspan=3, pady=5)
        self.enter_button = ttk.Button(button_frame, text=_('ENTER'),
                                       command=lambda: self.verify_transaction(transaction))
        self.cancel_button = ttk.Button(button_frame, text=_('CANCEL'),
                                        command=lambda: self.close_window(self.win))

        self.enter_button.pack(side='left')
        self.cancel_button.pack(side='left')

        self.date_input.focus()

    # Within the transaction windows, funds appear dynamically, if appropriate
    # This creates those buttons
    def create_frame_buttons(self, frame, buttons, transactions, variables, amounts):
        num_val = (self.win.register(num_validation), '%S')

        for i in range(len(transactions)):  # i is numerical
            variables.append(tk.BooleanVar())
            # if a fund is an additional currency, create an exrate prompt
            if transactions[i][:4] in self.settings['accounts']['assets']:
                if transactions[i][:4] != "1010":
                    amounts.append((ttk.Label(frame, text=_('Amount'), style="color.TLabel"),
                                    tk.StringVar(),  # will be connected to the Amount Entry
                                    ttk.Entry(frame, font=(self.FONT, self.SIZE), width=8,
                                              validate='key', validatecommand=num_val),
                                    ttk.Label(frame, text=_('ExRate'), style="color.TLabel"),
                                    tk.StringVar(),  # will be connected to the ExRate Entry
                                    ttk.Entry(frame, font=(self.FONT, self.SIZE), width=4,
                                              validate='key', validatecommand=num_val),
                                    tk.StringVar(),  # will be connected to the Label Entry
                                    ttk.Label(frame, style="color.TLabel")))  # Label shows the base amount
                    #  setting the StringVars to Entries
                    amounts[-1][2].config(textvariable=amounts[-1][1])
                    amounts[-1][5].config(textvariable=amounts[-1][4])
                    amounts[-1][7].config(textvariable=amounts[-1][6])

                    # set to ''
                    amounts[-1][1].set('')
                    amounts[-1][4].set('')
                    amounts[-1][6].set('')
                    #  tracing the StringVars so that the Base Label can be updated
                    amounts[-1][1].trace_variable('w', lambda x, y, z: self.update_base_label(amounts[-1]))
                    amounts[-1][4].trace_variable('w', lambda x, y, z: self.update_base_label(amounts[-1]))
                else:  # if 1010 (Base Currency)
                    amounts.append((ttk.Label(frame, text=_('Amount'), style="color.TLabel"),
                                    tk.StringVar(),
                                    ttk.Entry(frame, font=(self.FONT, self.SIZE), width=8,
                                              validate='key', validatecommand=num_val)))
                    # setting the StringVars to Entries
                    amounts[-1][2].config(text=amounts[-1][1])
            # if not an additional currency
            else:
                amounts.append((ttk.Label(frame, text=_('Amount'), style="color.TLabel"),
                                tk.StringVar(),
                                ttk.Entry(frame, font=(self.FONT, self.SIZE), width=8,
                                          validate='key', validatecommand=num_val)))
                # setting the StringVars to Entries
                amounts[-1][2].config(text=amounts[-1][1])

            if frame == self.debit_frame:
                buttons.append(tk.Checkbutton(frame, text=transactions[i], variable=variables[-1],
                                              onvalue=True, offvalue=False, width=25,
                                              anchor='c', justify='left', takefocus=0,
                                              command=lambda i=i: update_trans_window_frames(i,
                                                                                             variables,
                                                                                             amounts),
                                              indicatoron=0, selectcolor=self.secondary))
            else:
                buttons.append(tk.Checkbutton(frame, text=transactions[i], variable=variables[-1],
                                              onvalue=True, offvalue=False, width=25,
                                              anchor='c', justify='left', takefocus=0,
                                              command=lambda i=i: update_trans_window_frames(i,
                                                                                             variables,
                                                                                             amounts),
                                              indicatoron=0, selectcolor=self.secondary))
            # write buttons on the page
            buttons[-1].grid(column=0, row=i, sticky='w', pady=2)

    # When something is entered into the alt. currency Entry, a Label appears giving the Base Amount
    def update_base_label(self, array):
        if array[1].get() != '':
            if array[4].get() != '':
                dec_amount = D(array[1].get()) * D(array[4].get())
                array[6].set('{}'.format(dec_amount.quantize(self.cents, decimal.ROUND_HALF_UP)))
            else:
                array[6].set(array[1].get())
        elif array[4].get() != '':
            array[6].set(array[4].get())
        else:
            array[6].set('')

    # Verifies Transactions after 'Enter' is clicked on the transaction window
    def verify_transaction(self, trans_type):
        d = 0  # debit totals
        c = 0  # credit totals
        debit_amounts = []
        credit_amounts = []
        debit_funds = []
        credit_funds = []
        date = format_date(self.date_input.get())

        if check_date(date):  # the date is real
            if len(self.memo_input.get()) > 0:  # there is something in the memo line

                # --- THIS IS WHERE WE CONVERT THE VALUES IN THE UI FOR SPECIFIC TRANSACTION FUNCTIONS --- #

                #  ------  offering
                if trans_type == 'offering':
                    for x in self.input_debit_amounts:  # for an item in debit amounts (amounts)
                        if len(x) == 8:  # alt. currency
                            if x[2].get() != '':
                                if x[5].get() != '':
                                    # record debit total
                                    d += D(x[2].get()) * D(x[5].get())
                                    # alt.currency is recorded as a tuple (amount, exrate)
                                    debit_amounts.append((x[2].get(), x[5].get()))
                                    debit_funds.append(self.debits[self.input_debit_amounts.index(x)])

                                else:
                                    mbox(_("Incompletion Error"),
                                         _("Please fill out exchange rate."),
                                         b1=_('Ok'), b2=None)
                                    self.logger.warning("Incompletion Error: exchange rate")
                                    return
                            elif x[5].get() != '':
                                mbox(_("Incompletion Error"),
                                     _("Please fill out the amount of the alternate currency."),
                                     b1=_('Ok'), b2=None)
                                self.logger.warning("Incompletion Error: alternate currency")
                                return
                        else:  # base currency
                            if x[2].get() != '':
                                # record debit total
                                d += D(x[2].get())
                                debit_amounts.append(x[2].get())
                                debit_funds.append(self.debits[self.input_debit_amounts.index(x)])
                    # remove '()' from single number items
                    if len(debit_funds) == 1:
                        debit_funds = debit_funds[0]
                    if len(debit_amounts) == 1:
                        debit_amounts = debit_amounts[0]
                    if len(debit_amounts) > 0:
                        self.add_offering(date, debit_funds, debit_amounts, self.memo_input.get())
                        self.win.destroy()
                        self.win_window_open = False
                        self.fund_page(self.page, _("General Ledger"), self.ledger)
                        self.populate_directory_amounts()
                    else:
                        return
                #  ------  another type of transaction
                else:
                    # Debits ---------
                    for x in self.input_debit_amounts:  # for an item in debit amounts (amounts)
                        if len(x) == 8:
                            if x[2].get() != '':
                                if x[5].get() != '':
                                    # record debit total
                                    d += D(x[2].get()) * D(x[5].get())
                                    # alt.currency is recorded as a tuple (amount, exrate)
                                    debit_amounts.append((x[2].get(), x[5].get()))
                                    debit_funds.append(self.debits[self.input_debit_amounts.index(x)])
                                else:
                                    mbox(_("Incompletion Error"),
                                         _("Please fill out exchange rate."),
                                         b1=_('Ok'), b2=None)
                                    self.logger.warning("Incompletion Error: exchange rate")
                                    return
                            elif x[5].get() != '':
                                mbox(_("Incompletion Error"),
                                     _("Please fill out the amount of the alternate currency."),
                                     b1=_('Ok'), b2=None)
                                self.logger.warning("Incompletion Error: alternate currency")
                                return
                        else:
                            if x[2].get() != '':
                                # record debit total
                                d += D(x[2].get())
                                debit_amounts.append(x[2].get())
                                debit_funds.append(self.debits[self.input_debit_amounts.index(x)])
                    # Credits ---------
                    for x in self.input_credit_amounts:
                        if len(x) == 8:
                            if x[2].get() != '':
                                if x[5].get() != '':
                                    # check to see if available
                                    currency_name = self.credits[self.input_credit_amounts.index(x)]
                                    if self.subtract_from_alt_currency_records(currency_name,
                                                                               x[2].get(), x[5].get()):
                                        # record debit total
                                        c += D(x[2].get()) * D(x[5].get())
                                        # alt.currency is recorded as a tuple (amount, exrate)
                                        credit_amounts.append((x[2].get(), x[5].get()))
                                        credit_funds.append(self.credits[self.input_credit_amounts.index(x)])
                                    else:
                                        return
                                else:
                                    mbox(_("Incompletion Error"),
                                         _("Please fill out exchange rate."),
                                         b1=_('Ok'), b2=None)
                                    self.logger.warning("Incompletion Error: exchange rate")
                                    return
                            elif x[5].get() != '':
                                mbox(_("Incompletion Error"),
                                     _("Please fill out the amount of the alternate currency."),
                                     b1=_('Ok'), b2=None)
                                self.logger.warning("Incompletion Error: alternate currency")
                                return
                        else:
                            if x[2].get() != '':
                                # record debit total
                                c += D(x[2].get())
                                credit_amounts.append(x[2].get())
                                credit_funds.append(self.credits[self.input_credit_amounts.index(x)])

                    if d - c == 0:  # if debits and credits equal each other (which they should)
                        #  remove '()' if there is only one number
                        if len(debit_funds) == 1:
                            debit_funds = debit_funds[0]
                        if len(credit_funds) == 1:
                            credit_funds = credit_funds[0]
                        if len(debit_amounts) == 1:
                            debit_amounts = debit_amounts[0]
                        if len(credit_amounts) == 1:
                            credit_amounts = credit_amounts[0]
                        if trans_type == 'income':
                            self.add_income(date, debit_funds, credit_funds, debit_amounts, credit_amounts,
                                            self.memo_input.get(), self.payee_input.get())
                        elif trans_type == 'expense':
                            if self.enough_funds(credit_funds, credit_amounts):  # if there is enough
                                self.add_expense(date, debit_funds, credit_funds, debit_amounts, credit_amounts,
                                                 self.memo_input.get(), self.payee_input.get())
                        elif trans_type == 'transfer':
                            if self.enough_funds(debit_funds, debit_amounts):  # if there is enough
                                self.add_transfer(date, debit_funds, credit_funds, debit_amounts, credit_amounts,
                                                  self.memo_input.get())
                        elif trans_type == 'exchange':
                            if self.enough_funds(credit_funds, credit_amounts):  # if there is enough
                                self.add_exchange(date, debit_funds, credit_funds, debit_amounts, credit_amounts,
                                                  self.memo_input.get())
                        # when all said and done
                        if self.payee_input.get() not in self.payee_names and len(self.payee_input.get()) > 0:
                            self.payee_names.append(self.payee_input.get())
                        self.win.destroy()
                        self.win_window_open = False
                        self.fund_page(self.page, _('General Ledger'), self.ledger)
                        self.populate_directory_amounts()
                    else:
                        mbox(_('Incompletion Error'),
                             _('Debits and Credits do not equal each other.'),
                             b1=_('Ok'), b2=None)
                        self.logger.warning("Incompletion Error: debits and credits don't equal:\n"
                                            "   D=%s, C=%s" % (d, c))
                        return
            else:
                self.logger.warning("Incompletion Error: description")
                desc = mbox(_('Incompletion Error'),
                            _('Please write a description.'),
                            b1=_('Ok'), b2=_('Cancel'), entry=True)
                if desc:
                    self.memo_input.insert(0, desc)
                return
        else:
            self.logger.warning("Incompletion Error: date")

            datestr = mbox(_('Incompletion Error'),
                           _('Please enter a real date.'),
                           b1=_('Ok'), b2=_('Cancel'), entry=True)
            if datestr:
                if check_date(datestr):
                    self.date_input.set(datestr)
            return

    # When an row is double-clicked from treeview, a new window appears showing all transactions for a particular
    # transaction
    def generate_ledger_window(self, valuestring):
        win = tk.Toplevel()
        win.configure(background=self.primary)

        center_window(win, width=500)

        title = ttk.Label(win, text=_('Excerpt of General Ledger'), justify='left', style="header.TLabel")
        date_label = ttk.Label(win, text=datetime.datetime.now().strftime("%Y-%m-%d"),
                               justify='left', style="color.TLabel")

        title.grid(column=0, row=0, sticky='w')
        date_label.grid(column=0, row=1, sticky='w')

        tree = ttk.Treeview(win)
        tree.grid(column=0, row=2)
        tree.config(columns=('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'))

        tree.heading('#0', text=_('#'), command=lambda: self.sort_column(self.tree, '#0', False))
        tree.heading('#1', text=_('Date'), command=lambda: self.sort_date_column(self.tree, '#1', False))
        tree.heading('#2', text=_('Account'), command=lambda: self.sort_column(self.tree, '#2', False))
        tree.heading('#3', text=_('Base'), command=lambda: self.sort_column(self.tree, '#3', False))
        tree.heading('#4', text=_('Debit'), command=lambda: self.sort_column(self.tree, '#4', False))
        tree.heading('#5', text=_('Credit'), command=lambda: self.sort_column(self.tree, '#5', False))
        tree.heading('#6', text=_('Ex-Rate'), command=lambda: self.sort_column(self.tree, '#6', False))
        tree.heading('#7', text=_('Memo'), command=lambda: self.sort_column(self.tree, '#7', False))
        tree.heading('#8', text=_('Payee'), command=lambda: self.sort_column(self.tree, '#8', False))
        tree.column('#0', stretch=False, width=50)
        tree.column('#1', stretch=False, width=90)
        tree.column('#2', stretch=False, width=150)
        tree.column('#3', stretch=False, width=85)
        tree.column('#4', stretch=False, width=95)
        tree.column('#5', stretch=False, width=95)
        tree.column('#6', stretch=False, width=45)
        tree.column('#7', stretch=False, width=150)
        tree.column('#8', stretch=False, width=120)

        for entry in self.ledger:
            if entry[0] == int(valuestring):
                a = list()
                a.append(entry[0])  # add transaction date because
                for x in entry[1:]:  # don't change transaction number
                    if x == 0:
                        a.append('')
                    elif x is None:
                        a.append('')
                    else:
                        a.append(x)
                # create a row & add odd or even tags to it (for coloring later)
                if len(tree.get_children('')) % 2 == 0:
                    tree.insert('', 'end', text=a[0], tags='evenrow',
                                values=(a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))
                else:
                    tree.insert('', 'end', text=a[0], tags='oddrow',
                                values=(a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))

            # color odd rows
            tree.tag_configure('oddrow', background=self.secondary)

    # Double Clicking a row in treeview
    def _on_doubleclick(self, *args):
        item = self.tree.selection()[0]
        self.generate_ledger_window(self.tree.item(item, 'text'))
        print(args)

    def _on_right_click(self, *args):
        self.tree.focus()
        self.tree.yview_moveto(1)
        print(args)

    # Enabling the ability for columns to sort alphabetically in treeview
    def sort_column(self, tv, col, reverse):
        array = [(tv.set(k, col), k) for k in tv.get_children('')]
        array.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(array):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(col, command=lambda col=col: self.sort_column(tv, col, not reverse))

    # When clicking on a 'date column' in the treeview, the date appropriate sorts
    # This puts the string value 'DD/MM/YYYY' into an actual date and then sorts those values
    def sort_date_column(self, tv, col, reverse):
        array = [(tv.set(k, col), k) for k in tv.get_children('')]
        array.sort(key=lambda x: datetime.datetime.strptime(x[0], '%d/%m/%Y'), reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(array):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(col, command=lambda col=col: self.sort_date_column(tv, col, not reverse))

    def callback(self, word):
        print(word)
        print(self.secondary)

    # Giving specific instructions when closing windows
    def close_window(self, window=None):
        if window is None:
            self.win_window_open = False
            self.win.destroy()
        else:
            self.win_window_open = False
            window.destroy()

    def on_exit(self):
        self.master.destroy()

    def search_treeview(self, item=''):
        pattern = self._toSearch.get()

        if len(pattern) > 0:
            children = self.tree.get_children(item)
            array = []
            for child in children:
                text = self.tree.item(child, 'values')

                for x in text:
                    if pattern.lower() in x.lower():
                        array.append(child)

            self.tree.selection_set(array)
        else:
            self.tree.selection_remove(self.tree.selection())

    # populates the labels that declare totals of all funds on menu frame
    def populate_directory_amounts(self):
        directory_amounts = []
        funds = self.get_funds()
        for x in funds:
            i = funds.index(x)
            directory_amounts.append(tk.Label(self.menu_directory_frame, font=(self.FONT, self.SIZE),
                                              bg=self.primary, width=8,
                                              borderwidth=2, relief='ridge'))
            directory_amounts[-1].grid(column=1, row=i+2, sticky='nse')
            try:
                directory_amounts[-1].configure(text=self.load_fund(x)[-1][4])
            except IndexError:
                directory_amounts[-1].configure(text=(format(0, '.2f')))

    # generate a report by calling the calculate_balance_sheet
    def generate_balance_report(self):
        try:
            document = '{} Balance Sheet.pdf'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
            filepath = filedialog.asksaveasfilename(initialdir=os.getcwd(), title="Select file",
                                                    defaultextension='.pdf',
                                                    initialfile=document,
                                                    filetypes=(("pdf files", "*.pdf"), ("all files", "*.*")))
            write_balance_sheet(self.settings['Church Name'], self.calculate_balance_sheet(),
                                filepath=filepath)
            logger.info("File %s created." % document)
        except FileNotFoundError:
            return

    # saves ledger and settings files
    def save_data(self):
        self.save_to_file(self.ledger, self.settings)
        time = datetime.datetime.now().strftime('%H:%M:%S')
        self.save_label.config(text=_('Last Saved {}').format(time))

    # clears name prompts saved in settings
    def clear_name_prompts(self):
        self.payee_names = []
        self.settings['payee_names'] = []

    # set up the settingUI window
    def set_settings_window(self, settings_type):
        # Configuration of Settings Window
        self.settings_window = tk.Toplevel()
        self.settings_window.protocol('WM_DELETE_WINDOW', lambda: self.close_window(self.settings_window))

        self.settings_window.title(_('Settings'))
        center_window(self.settings_window, width=500, height=400)
        self.settings_window.configure(background=self.primary)

        # Main Frame Configurations
        self.main_frame = ttk.Frame(self.settings_window, style="color.TFrame")
        self.main_frame.grid(column=0, row=0, sticky='nsew', padx=5, pady=5)

        if settings_type == "fund_accounts":
            self.set_accounts_menu()
        elif settings_type == "offering":
            self.set_offering_menu()
        elif settings_type == "language":
            self.change_language_settings()
        elif settings_type == "church_name":
            self.change_church_name()

    # set up window so that the user can change the language
    def change_language_settings(self):
        self.main_frame.grid_forget()

        # Main Frame
        self.main_frame = ttk.Frame(self.settings_window, style="color.TFrame")
        self.main_frame.pack(padx=5, pady=5)

        title = ttk.Label(self.main_frame, text="Change Language", style="header2.TLabel")
        title.pack()

        langs = [self.language_values[x] for x in self.language_values]
        cb = ttk.Combobox(self.main_frame, values=langs,
                          exportselection=0, state='readonly')
        cb.set(self.language_values[self.settings['language']])
        cb.option_add("*TCombobox*Listbox.selectBackground", self.secondary)
        cb.option_add("*TCombobox*Listbox.selectForeground", "#000000")

        cb.pack(pady=15)

        # SAVE & CLOSE BUTTONS
        button_frame = ttk.Frame(self.main_frame, style="color.TFrame")
        button_frame.pack()
        save_button = ttk.Button(button_frame, text=_('Enter'),
                                 command=lambda: self.save_information('language', cb.get(), self.settings_window))
        close_window_button = ttk.Button(button_frame, text=_('Cancel'), command=self.settings_window.destroy)
        close_window_button.pack(side='right')
        save_button.pack(side='right')

    # set up window so user can change the church name
    def change_church_name(self):
        self.main_frame.grid_forget()

        # Main Frame
        self.main_frame = ttk.Frame(self.settings_window, style="color.TFrame")
        self.main_frame.pack(padx=5, pady=5)

        title = ttk.Label(self.main_frame, text="Change the Name of the Church", style="header2.TLabel")
        title.pack()

        namevar = self.settings["Church Name"]
        text = ttk.Entry(self.main_frame, font=(self.FONT, self.SIZE+2), width=30)
        text.insert(0, namevar)
        text.pack(pady=15)

        # SAVE & CLOSE BUTTONS
        button_frame = ttk.Frame(self.main_frame, style="color.TFrame")
        button_frame.pack()
        save_button = ttk.Button(button_frame, text=_('Enter'),
                                 command=lambda: self.save_information('church name', text.get(), self.settings_window))
        close_window_button = ttk.Button(button_frame, text=_('Cancel'), command=self.settings_window.destroy)
        close_window_button.pack(side='right')
        save_button.pack(side='right')

    # save settings information
    def save_information(self, category, value, window):
        if category == "language":
            for lang in self.language_values:
                if self.language_values[lang] == value:
                    self.settings['language'] = lang
                    self.save_all_to_file()
                    get_language()
                    self.page_title = ""
                    self.start_ui(self.master)
                    break
        elif category == "church name":
            if len(value) > 0:
                self.settings["Church Name"] = value
                self.save_all_to_file()
                self.start_ui(self.master)
            else:
                mbox(_("Input Needed"), _("Please enter a name."), b1=_('Ok'), b2=None)
                return
        window.destroy()

    # open winodow for user to change account and fund changes
    def set_accounts_menu(self):
        # Delete unused items
        self.main_frame.grid_forget()

        # MAIN Frame
        self.main_frame = ttk.Frame(self.settings_window, width=560, style="color.TFrame")
        self.main_frame.grid(column=0, row=1, sticky='nsew', padx=5, pady=5)

        # TITLE FRAME
        title_frame = ttk.Frame(self.main_frame, borderwidth=2, relief='ridge', style="color.TFrame")
        title_frame.grid(column=0, row=1, sticky='nswe', columnspan=2)

        # Title
        main_title = ttk.Label(title_frame, text=_('Fund & Account Settings'), style="header.TLabel")
        main_title.pack(anchor='w')

        # Account Category Menu buttons - Assets, Liabilities, Equities, Revenues, Expenses
        buttons = []
        for acc in self.account_keys:
            buttons.append(ttk.Button(title_frame, text=acc.title(),
                                      command=lambda acc=acc: self.display_account(acc)))
            buttons[-1].pack(side='left', fill='x', expand=1)

        # Canvas to place accounts
        self.account_frame = ttk.Frame(self.main_frame, style="color.TFrame")
        self.account_frame.grid(column=0, row=2)
        self.display_account('assets')

    # When a category button is selected, two frames appear and buttons on the bottom of the page
    def display_account(self, account):
        # Check for and delete all previous children
        if self.account_frame.winfo_children():
            for child in self.account_frame.winfo_children():
                child.destroy()

        # create widgets
        buttons = []
        # frame for accounts in category
        frame = ttk.LabelFrame(self.account_frame, text=account.title(), borderwidth=2, relief='sunken',
                               style="color.TLabelframe")
        frame.grid(column=0, row=0, sticky='nsew', rowspan=3, padx=5, pady=10)
        frame.grid_propagate(0)

        self.fund_box = tk.Listbox(frame, borderwidth=0, height=9, selectbackground=self.secondary,
                                   selectforeground="#000000")
        self.fund_box.pack(anchor='w', side='top', fill='both', expand=1)
        if len(self.settings['accounts'][account]) > 0:
            for x in self.settings['accounts'][account]:
                words = '{} {}'.format(x, self.settings['accounts'][account][x][0])
                self.fund_box.insert('end', words)

        # frame for description of funds
        desc_frame = ttk.LabelFrame(self.account_frame, text=_('Description'), borderwidth=2, relief='sunken',
                                    style="color.TLabelframe")
        desc_frame.grid(column=1, row=0, sticky='nsew', columnspan=3, padx=5, pady=10)
        desc_frame.grid_propagate(0)
        self.desc_account = tk.Text(desc_frame, width=40, height=4, font=(self.FONT, self.SIZE), wrap='word')
        self.desc_account.pack(pady=0, fill='both', expand=1)
        self.desc_label = tk.Text(desc_frame, width=40, height=5, font=(self.FONT, self.SIZE), wrap='word')
        self.desc_label.pack(pady=0, fill='both', expand=1)

        self.edit_label(self.desc_account, self.fund_definitions[account])
        self.edit_label(self.desc_label, _('Double-click on a fund to read more about it.'))

        self.fund_box.bind('<Double-Button-1>', lambda _: self.edit_label(account=account))

        # Buttons at the bottom of the page
        button_frame = ttk.Frame(self.account_frame)
        buttons.append(ttk.Button(button_frame, text=_('Add a Fund'),
                                  command=lambda: self.create_a_fund(_("Add a fund to %s" % account.title()),
                                                                     account)))
        buttons.append(ttk.Button(button_frame, text=_('Remove a Fund'),
                                  command=lambda: self.remove_a_fund(account)))
        buttons.append(ttk.Button(button_frame, text=_('Edit a Fund'),
                                  command=lambda: self.edit_a_fund(account)))
        buttons.append(ttk.Button(button_frame, text=_('Close Window'), command=self.settings_window.destroy))
        button_frame.grid(column=0, row=3, columnspan=4, padx=10, pady=2)
        for button in buttons:
            button.grid(column=buttons.index(button), row=0)

        # Authorize Frame
        if self.authorize_user():
            for button in buttons:
                button.config(state='normal')
        else:
            for button in buttons:
                button.config(state='disable')

    # A window appears for the creation of a fund
    def create_a_fund(self, message, account):
        # Build frame & widgets
        frame = tk.Toplevel()
        frame.title(_('Create A Fund'))
        frame.configure(background=self.primary, padx=5, pady=5)

        center_window(frame)

        # widgets
        header = ttk.Label(frame, text=message, style="header.TLabel")
        header.grid(column=0, row=0, columnspan=3)
        numb_lb = ttk.Label(frame, text=_('Fund Number'), style="color.TLabel")
        numb_ent = ttk.Entry(frame, width=6, font=(self.FONT, self.SIZE))
        name_lb = ttk.Label(frame, text=_('Fund Name'), style="color.TLabel")
        name_ent = ttk.Entry(frame, width=20, font=(self.FONT, self.SIZE))
        desc_lb = ttk.Label(frame, text=_('Fund Description'), style="color.TLabel")
        desc_ent = ttk.Entry(frame, font=(self.FONT, self.SIZE))

        # show currency options if account = assets
        cur_values = ['{} ({})'.format(s, self.shadow_dict[s]) for s in self.shadow_dict]
        for currency in self.settings['accounts']['assets']:
            if self.settings['accounts']['assets'][currency][2] in cur_values:
                cur_values.remove(self.settings['accounts']['assets'][currency][2])

        currency_lb = ttk.Label(frame, text=_('Currency of Account'), style="color.TLabel")
        currency_cb = ttk.Combobox(frame, state='readonly', exportselection=0, width=35,
                                   values=cur_values, font=(self.FONT, self.SIZE))
        currency_cb.option_add("*TCombobox*Listbox.selectBackground", self.secondary)
        currency_cb.option_add("*TCombobox*Listbox.selectForeground", "#000000")

        # combobox for currency selection
        if account == "assets":
            currency_lb.grid(column=0, row=5, columnspan=2, sticky='w')
            currency_cb.grid(column=0, row=6, columnspan=3, sticky='we')
            name_ent.insert(0, 'Cash ')
        else:
            currency_lb.grid_forget()
            currency_cb.grid_forget()
            name_ent.delete(0, 'end')

        enter_button = ttk.Button(frame, text=_('Enter & Save'),
                                  command=lambda: self.fund_creation(frame, account, numb_ent.get(),
                                                                     name_ent.get(), desc_ent.get(),
                                                                     currency_cb.get()))
        cancel_button = ttk.Button(frame, text=_('Cancel'), command=frame.destroy)

        # Figure out the fund number by asset
        y = 0
        for x in self.settings['accounts'][account]:
            if int(x) % 10 == 0:  # get the highest number that divides by 10
                y = int(x)
        if y > 1000:  # if y changed
            if (y + 10) < (int(str(y)[0]) * 1000 + 1000):  # if the number plus 10 is less than the next thousand
                numb_ent.insert(0, y + 10)
        else:
            if account == 'assets':
                numb_ent.insert(0, 1010)
            elif account == 'liabilities':
                numb_ent.insert(0, 2010)
            elif account == 'equitites':
                numb_ent.insert(0, 3010)
            elif account == 'revenues':
                numb_ent.insert(0, 4010)
            elif account == 'expeneses':
                numb_ent.insert(0, 6010)

        # widget.grid
        numb_lb.grid(column=0, row=1, sticky='w')
        numb_ent.grid(column=0, row=2, sticky='we')
        name_lb.grid(column=1, row=1, sticky='w')
        name_ent.grid(column=1, row=2, sticky='we', columnspan=2)
        desc_lb.grid(column=0, row=3, sticky='w', columnspan=2)
        desc_ent.grid(column=0, row=4, sticky='we', columnspan=3)
        enter_button.grid(column=1, row=7, pady=10)
        cancel_button.grid(column=2, row=7, pady=10)

    # A window appears to edit a fund name and description
    def edit_a_fund(self, account):

        if self.fund_box.curselection():
            number = self.fund_box.get('active')[:4]
        else:
            mbox(_('Selection Error'), _('There is no fund selected'), b2=None)
            return
        # Build frame & widgets
        frame = tk.Toplevel()
        frame.title(_('Edit A Fund'))
        frame.configure(background=self.primary, padx=5, pady=5)

        center_window(frame)

        # widgets
        header = ttk.Label(frame, text=_('Edit a Fund'), style="header.TLabel")
        header.grid(column=0, row=0, columnspan=3)
        numb_lb = ttk.Label(frame, text=_('Fund Number'), style="color.TLabel")
        numb_ent = ttk.Entry(frame, width=6, font=(self.FONT, self.SIZE))
        name_lb = ttk.Label(frame, text=_('Fund Name'), style="color.TLabel")
        name_ent = ttk.Entry(frame, width=20, font=(self.FONT, self.SIZE))
        desc_lb = ttk.Label(frame, text=_('Fund Description'), style="color.TLabel")
        desc_ent = ttk.Entry(frame, font=(self.FONT, self.SIZE))

        numb_ent.insert(0, number)
        name_ent.insert(0, self.settings['accounts'][account][number][0])
        desc_ent.insert(0, self.settings['accounts'][account][number][3])

        enter_button = ttk.Button(frame, text=_('Enter & Save'),
                                  command=lambda: self.fund_editor(frame, account, numb_ent.get(),
                                                                   name_ent.get(), desc_ent.get()))
        cancel_button = ttk.Button(frame, text=_('Cancel'), command=frame.destroy)

        # widget.grid
        numb_lb.grid(column=0, row=1, sticky='w')
        numb_ent.grid(column=0, row=2, sticky='we')
        name_lb.grid(column=1, row=1, sticky='w')
        name_ent.grid(column=1, row=2, sticky='we', columnspan=2)
        desc_lb.grid(column=0, row=3, sticky='w', columnspan=2)
        desc_ent.grid(column=0, row=4, sticky='we', columnspan=3)
        enter_button.grid(column=1, row=7, pady=10)
        cancel_button.grid(column=2, row=7, pady=10)

    # Create the fund after the create-a-fund application is filled out
    def fund_creation(self, frame, account, number, name, description, currency=None):
        # create fund in file
        if fund_entry_checker(number, name, description):
            if account == "assets":
                if currency != '':
                    if name == "Cash":
                        name = name + " " + currency[-4:-1]
                    elif name == "Cash ":
                        name = name + " " + currency[-4:-1]
                    self.settings['accounts']["assets"][number] = [name, {}, currency, description]
                else:
                    mbox(_('Currency Needed'),
                         _('Please select a currency from the list.'),
                         b1=_('Ok'), b2=None)
                    return
            else:
                self.settings['accounts'][account][number] = [name, 0, 0, description]

            # add fund to combobox (to visualize the change)
            try:
                self.fund_box.insert('end', '{} {}'.format(number, name))
                array = list()
                for x in self.fund_box.get(0, 'end'):
                    array.append(x)
                array.sort()
                self.fund_box.delete(0, 'end')
                for x in array:
                    self.fund_box.insert('end', x)
            except AttributeError:  # A currency was added, not a fund
                pass
            self.logger.info("Added %s %s to %s" % (number, name, account))
            try:
                self.populate_fund_menu_directory(self.menu_directory_frame)
            except AttributeError:
                pass

            self.save_all_to_file()

            # Destroy 'Create-a-Fund Frame' last
            frame.destroy()

    # edits the funds in the funds and accounts window
    def fund_editor(self, frame, account, number, name, description):
        if fund_entry_checker(number, name, description):
            self.settings['accounts'][account][number][0] = name
            self.settings['accounts'][account][number][3] = description

            frame.destroy()

    # Remove a fund from the acocunts window
    def remove_a_fund(self, account):
        if account == 'assets':
            if self.fund_box.get('active')[:4] == '1010':
                mbox(_('Error'), _('You cannot delete the base currency.\n'
                                   'If you want to change the base currency, '
                                   'create a new Ledger.'),
                     b1=_('Ok'), b2=None)
                return
        deletion = mbox(_('Delete Warning'), _("Are you sure that you want to delete this fund?"),
                        b1=_('Yes'), b2=_('No'))
        if deletion:
            if self.fund_box.curselection():
                item = self.fund_box.curselection()
                name = self.fund_box.get(item)
                for x in self.settings['accounts'][account]:
                    if x == name[:4]:
                        del self.settings['accounts'][account][name[:4]]
                        self.logger.info("Deleted %s from %s" % (name, account))
                        self.fund_box.delete(item)
                        self.populate_fund_menu_directory(self.menu_directory_frame)
                        break
        else:
            return

    # opens window so the user can change offering settings
    def set_offering_menu(self):
        self.main_frame.grid_forget()

        num_val = (self.main_frame.register(num_validation), '%S')

        # MAIN Frame
        self.main_frame = ttk.Frame(self.settings_window, width=560, height=400, style="color.TFrame")
        self.main_frame.pack()

        # Write Title
        main_title = ttk.Label(self.main_frame, text=_('Distribution of Tithes & Offerings'), style="header.TLabel")
        main_title.grid(column=0, row=0, sticky='w', columnspan=2, pady=5)

        allocation_frame = ttk.LabelFrame(self.main_frame, text=_("Enable Allocation Deduction"),
                                          style="color.TLabelframe")
        allocation_frame.grid(column=0, row=1, sticky='we', pady=10, padx=5)

        allo_var = tk.IntVar()
        allocation_cb = ttk.Checkbutton(allocation_frame, text=_('Automatically deduct allocations from the offering'),
                                        variable=allo_var)
        allo_var.set(self.settings['allocations'][0])
        self.wef_str = tk.StringVar()
        self.dist_str = tk.StringVar()
        self.edu_str = tk.StringVar()

        # Populate values for allocations from Settings
        self.wef_str.set(self.settings['allocations'][1]['WEF'])
        self.dist_str.set(self.settings['allocations'][1]['District'])
        self.edu_str.set(self.settings['allocations'][1]['Education'])

        wef = [ttk.Label(allocation_frame, text=_('WEF'), style="color.TLabel"),
               ttk.Label(allocation_frame, text=_('%'), style="color.TLabel"),
               ttk.Entry(allocation_frame, font=(self.FONT, self.SIZE), width=4,
                         validatecommand=num_val, validate='key', textvariable=self.wef_str)]
        dist = [ttk.Label(allocation_frame, text=_('District'), style="color.TLabel"),
                ttk.Label(allocation_frame, text=_('%'), style="color.TLabel"),
                ttk.Entry(allocation_frame, font=(self.FONT, self.SIZE), width=4,
                          validatecommand=num_val, validate='key', textvariable=self.dist_str)]
        edu = [ttk.Label(allocation_frame, text=_('Education'), style="color.TLabel"),
               ttk.Label(allocation_frame, text=_('%'), style="color.TLabel"),
               ttk.Entry(allocation_frame, font=(self.FONT, self.SIZE), width=4,
                         validatecommand=num_val, validate='key', textvariable=self.edu_str)]

        allo_var.trace_variable('w', lambda x, y, z: self.change_allo_setting(allo_var.get(),
                                                                              wef[2], dist[2], edu[2]))

        allocation_cb.grid(column=0, row=0, columnspan=6)
        wef[0].grid(column=0, row=1, columnspan=2)
        wef[1].grid(column=1, row=2, sticky='w')
        wef[2].grid(column=0, row=2, sticky='e')
        dist[0].grid(column=2, row=1, columnspan=2)
        dist[1].grid(column=3, row=2, sticky='w')
        dist[2].grid(column=2, row=2, sticky='e')
        edu[0].grid(column=4, row=1, columnspan=2)
        edu[1].grid(column=5, row=2, sticky='w')
        edu[2].grid(column=4, row=2, sticky='e')

        ael = ttk.Frame(allocation_frame, style="color.TFrame")
        ael.grid(column=6, row=0, sticky='e', rowspan=4)
        explanation = _("Enabling allocations removes the amounts separate from operating funds.")
        allo_explain = ttk.Label(ael, text=explanation, wraplength=120, justify='left', style="color.TLabel")
        allo_explain.pack(anchor='e', padx=20)

        # DISTRIBUTING FUNDS
        self.distributed_funds_frame = ttk.LabelFrame(self.main_frame, text=_('Distributed Funds'),
                                                      style="color.TLabelframe")
        self.distributed_funds_frame.grid(column=0, row=3, sticky='we', padx=5, pady=5)

        self.set_distribute_funds_frame(self.distributed_funds_frame)

        # Authorize Frame
        if self.authorize_user():
            allocation_cb.configure(state='normal')
            wef[2].configure(state='normal')
            dist[2].configure(state='normal')
            edu[2].configure(state='normal')
            for x in self.percentages:
                x[1].configure(state='normal')
            for x in self.amounts:
                x[1].configure(state='normal')
            self.keep_funds_button.configure(state='normal')
        else:
            allocation_cb.configure(state='disable')
            wef[2].configure(state='readonly')
            dist[2].configure(state='readonly')
            edu[2].configure(state='readonly')
            for x in self.percentages:
                x[1].configure(state='readonly')
            for x in self.amounts:
                x[1].configure(state='readonly')
            self.keep_funds_button.configure(state='disable')

    # changes offering window when buttons are clicked to remove allocation dependency
    def set_distribute_funds_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()

        perc_label = ttk.Label(frame, text=_('%*'), style="color.TLabel")
        perc_label.grid(column=1, row=0)
        amount_label = ttk.Label(frame, text=_('Amount**'), style="color.TLabel")
        amount_label.grid(column=2, row=0)

        # Totals
        self.tot_per = tk.StringVar()
        self.tot_amt = tk.StringVar()
        # track so doesn't go over 100
        self.tot_per.trace_variable('w', lambda x, y, z: turn_red(self.tot_per, self.tot_per_label))

        self.total_label = ttk.Label(frame, text=_('Total'), style="color.TLabel")
        self.tot_per_label = ttk.Label(frame, textvariable=self.tot_per, style="color.TLabel")
        self.tot_amt_label = ttk.Label(frame, textvariable=self.tot_amt, style="color.TLabel")

        # Accounts
        labels = []
        self.percentages = []
        self.amounts = []
        fund_array = []
        for acc in self.settings['accounts']['equities']:
            name = '{} {}'.format(acc, self.settings['accounts']['equities'][acc][0])
            if self.settings['allocations'][0] == 1:
                if 'WEF' in name:
                    pass
                elif 'District' in name:
                    pass
                elif 'Education' in name:
                    pass
                else:
                    fund_array.append((acc, name))
            else:
                fund_array.append((acc, name))

        fund_array.sort()
        for x, y in fund_array:
            num_val = (frame.register(num_validation), '%S')  # number input only

            labels.append(ttk.Label(frame, text=y, style="color.TLabel"))
            self.percentages.append([tk.StringVar(),
                                     ttk.Entry(frame, width=5, font=(self.FONT, self.SIZE),
                                               validatecommand=num_val, validate='key')])
            self.percentages[-1][0].trace_variable('w', lambda x, y, z: set_total_label(self.tot_per,
                                                                                        self.percentages))
            self.percentages[-1][0].set(self.settings['accounts']['equities'][x][1])
            self.percentages[-1][1].config(textvariable=self.percentages[-1][0])
            self.amounts.append([tk.StringVar(),
                                 ttk.Entry(frame, width=5, font=(self.FONT, self.SIZE),
                                           validatecommand=num_val, validate='key')])
            self.amounts[-1][0].trace_variable('w', lambda x, y, z: set_total_label(self.tot_amt,
                                                                                    self.amounts))
            self.amounts[-1][0].set(self.settings['accounts']['equities'][x][2])
            self.amounts[-1][1].config(textvariable=self.amounts[-1][0])
            labels[-1].grid(column=0, row=len(labels), sticky='w')
            self.percentages[-1][1].grid(column=1, row=len(labels), sticky='w')
            self.amounts[-1][1].grid(column=2, row=len(labels), sticky='w', padx=5)

        # Grid Totals
        self.total_label.grid(column=0, row=len(labels) + 1, sticky='e')
        self.tot_per_label.grid(column=1, row=len(labels) + 1, sticky='w')
        self.tot_amt_label.grid(column=2, row=len(labels) + 1, sticky='w', padx=5)

        desc_fr = ttk.Frame(frame, style="color.TFrame")
        desc_fr.grid(column=3, row=0, rowspan=10)
        desc_df_text = _("After offering is collected, the money will be distributed in the "
                         "funds of your choosing as 'operating funds'. \n*Please select the "
                         "percentage of funds equaling 100%. \n**If you prefer to enter a "
                         "specific amount, this amount will be deducted from the operating funds "
                         "first, if available. Then operating funds will be distributed by "
                         "percentage into the remaining categories.")
        desc_per = ttk.Label(desc_fr, text=desc_df_text, wraplength=200, justify='left', style="color.TLabel")
        desc_per.pack(padx=30, pady=10)

        self.keep_funds_button = ttk.Button(desc_fr, text=_('Save Changes'), style='my.TButton',
                                            command=lambda: self.keep_fund_changes(fund_array))
        close_window_button = ttk.Button(desc_fr, text=_('Close Window'), style='my.TButton',
                                         command=self.settings_window.destroy)
        self.keep_funds_button.pack(side='left', padx=30, pady=15)
        close_window_button.pack(side='left', padx=30, pady=15)

    # change the allocation dependency
    def change_allo_setting(self, x, wef, dist, edu):
        # change value in settings
        self.settings['allocations'][0] = x
        # recalcuate funds for frame
        self.set_distribute_funds_frame(self.distributed_funds_frame)

        # Enable or disable Entry widgets in the Allocation Frame
        if x:
            wef.config(state='normal')
            dist.config(state='normal')
            edu.config(state='normal')
        else:
            wef.config(state='disable')
            dist.config(state='disable')
            edu.config(state='disable')

    # edits the label in the funds and accounts change window
    def edit_label(self, label=None, text="", account=None):
        if account:
            if not text:
                try:
                    text = self.settings['accounts'][account][self.fund_box.get('active')[:4]][3]
                except KeyError:
                    text = _('Click on a fund to read more about it.')
        if label is None:
            label = self.desc_label
        label.config(state='normal')
        label.delete(1.0, 'end')
        label.insert('end', text)
        label.config(state='disabled')

    # saves the changes in offering change window
    def keep_fund_changes(self, array):
        for x in range(len(array)):
            if self.percentages[x][0].get():
                self.settings['accounts']['equities'][array[x][0]][1] = int(self.percentages[x][0].get())
            else:
                self.settings['accounts']['equities'][array[x][0]][1] = 0
            if self.amounts[x][0].get():
                self.settings['accounts']['equities'][array[x][0]][2] = int(self.amounts[x][0].get())
            else:
                self.settings['accounts']['equities'][array[x][0]][2] = 0
        mbox(_('Attention'), _('Changes Saved!'), b2=None)

    # checks to see if user is authorized
    # unused at the moment
    def authorize_user(self):
        authorized = ['Default User']
        if self.user in authorized:
            return True
        else:
            return False

    # placeholder
    def throwaway(self):
        self.logger.info('thrown')

    # saves settings
    def save_all_to_file(self):
        # save settings to file
        with open('resources/settings.json', 'w+', encoding='utf-8') as doc1:
            json.dump(self.settings, doc1, indent=2)


# Creates a directory for a user to import an older ledger
def import_ledger_file():
    warning = _("By importing a new ledger, you will delete unsaved information. Do you want to continue?")
    check = mbox(_('Deletion Warning'), warning,
                 b1=_('Yes'), b2=_('No'))
    if check:
        try:
            filepath = filedialog.askopenfilename(initialdir=os.getcwd(), title='Open Ledger File',
                                                  filetypes=(("text files", "*.txt"), ("all files", "*.*")))
            upload_ledger(filepath)
            logger.info("User uploaded a new ledger document. \n%s" % filepath)
        except FileNotFoundError:
            return
    else:
        return


# checks funds entered in funds & accounts window
def fund_entry_checker(number, name, description):
    if len(number) < 4:
        mbox(_('Input Error'),
             _('Please write a four-digit account number.'),
             b1=_('Ok'), b2=None)
        return False

    if len(name) < 1:
        mbox(_('Input Error'),
             _('Please input a name for the account.'),
             b1=_('Ok'), b2=None)
        return False

    if len(description) < 1:
        mbox(_('Input Error'),
             _('Please input a description for the account.'),
             b1=_('Ok'), b2=None)
        return False
    return True


# Gives information about the program
def about():
    message = (_('Church Financial Accountability Program\nVersion {}\nCopyright 2018 (c) Joseph Sumi')
               .format(BaseProgram.version))
    mbox(_('About'), message,
         b1=_('Ok'), b2=None)


# Function is called from a checkbutton to update widgets on a frame
def update_trans_window_frames(i, variable, amounts):
    if variable[i].get():  # if the checkbutton pressed
        if len(amounts[i]) > 3:  # alt. currencies
            amounts[i][0].grid(column=1, row=i, sticky='w')
            amounts[i][2].grid(column=2, row=i, sticky='w')
            amounts[i][3].grid(column=3, row=i, sticky='w')
            amounts[i][5].grid(column=4, row=i, sticky='w')
            amounts[i][7].grid(column=5, row=i, sticky='w')
        else:  # other funds
            amounts[i][0].grid(column=1, row=i, sticky='w')
            amounts[i][2].grid(column=2, row=i, sticky='w')
    else:  # delete when checkbutton unpressed
        if len(amounts[i]) > 3:  # alt. currencies
            amounts[i][0].grid_forget()
            amounts[i][1].set('')
            amounts[i][2].grid_forget()
            amounts[i][3].grid_forget()
            amounts[i][4].set('')
            amounts[i][5].grid_forget()
            amounts[i][7].grid_forget()
        else:  # other funds
            amounts[i][0].grid_forget()
            amounts[i][1].set('')
            amounts[i][2].grid_forget()


# totals the available values for offering settings
def set_total_label(my_var, my_list):
    x = D('0')
    for g in my_list:
        if g[0].get() != '':
            x += D(g[0].get())
    my_var.set(str(D(x).quantize(D('.1'), decimal.ROUND_HALF_UP)))


# changes colors of variables for offering settings
def turn_red(my_var, my_var_label):
    try:
        if int(my_var.get()) > 100:
            my_var_label.configure(foreground='red')
        elif int(my_var.get()) == 100:
            my_var_label.configure(foreground='green3')
        elif int(my_var.get()) == 0:
            my_var_label.configure(foreground='red')
        else:
            my_var_label.configure(foreground='blue')
    except ValueError:
        if float(my_var.get()) > 100:
            my_var_label.configure(foreground='red')
        elif float(my_var.get()) == 100:
            my_var_label.configure(foreground='green3')
        elif float(my_var.get()) == 0:
            my_var_label.configure(foreground='red')
        else:
            my_var_label.configure(foreground='blue')


# loads dictionary of currencies
def currency_dictionary():
    with open('resources/currency_dict.json', 'r', encoding='utf-8') as doc:
        data = json.load(doc)
    return data


# loads data from the matrix
def extract_data(matrix_name):
    with open('CFAP_data.txt', 'r+', encoding='utf-8') as doc:
        try:
            f = json.load(doc)
            return f[f.index(matrix_name)]
        except IndexError:
            return None


# Enables entries to only accept numerical values and '.'
def num_validation(value):
    if value == '.':
        return True
    elif value.isnumeric():
        return True
    else:
        return False


# Centers the window in the middle of the screen
def center_window(frame, width=None, height=None):
    # Gets the requested values of the height and width.
    if width is None:
        window_width = frame.winfo_reqwidth()
    else:
        window_width = width
    if height is None:
        window_height = frame.winfo_reqheight()
    else:
        window_height = height

    # Gets both half the screen width/height and window width/height
    position_right = int(root.winfo_screenwidth() // 2 - window_width // 2)
    position_down = int(root.winfo_screenheight() // 2 - window_height // 2)

    # Positions the window in the center of the page.
    frame.geometry("+{}+{}".format(position_right, position_down))


# placeholder
def placeholder():
    print(u'Лорем ипсум долор сит амет, пер цлита поссит ех, ат мунере фабулас петентиум сит.'
          u'Иус цу цибо саперет сцрипсерит, нец виси муциус лабитур ид. Ет хис нонумес нолуиссе дигниссим. ')


# Makes sure that Date format for the string is a proper DD/MM/YYYY format and
# changes the format to fit this description
def format_date(date):
    if len(date) < 10:  # add '0' to stringdate where necessary
        if (len(date) - date.rfind('/')) == 3:
            date = date[:date.rfind('/')+1] + '20' + date[date.rfind('/')+1:]
            if date.find('/') == 1:  # search for the first /
                date = '0' + date
                if date.rfind('/') == 4:
                    date = date[:3] + '0' + date[3:]
                    return date
                else:
                    return date
            else:  # search for the second /
                if date.rfind('/') == 4:
                    date = date[:3] + '0' + date[3:]
                    return date
                else:
                    return date
        else:
            if date.find('/') == 1:  # search for the first /
                date = '0' + date
                if date.rfind('/') == 4:
                    date = date[:3] + '0' + date[3:]
                    return date
                else:
                    return date
            else:  # search for the second /
                if date.rfind('/') == 4:
                    date = date[:3] + '0' + date[3:]
                    return date
                else:
                    return date
    else:
        return date


# Setting up the logging protocols by importing them from a local json file
def setup_logging(default_path='resources/log.json', default_level=logging.INFO, env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

D = decimal.Decimal

# hook
sys.excepthook = lambda exc, val, tb: exception_hook(logger, exc, val, tb)
# tk_hook
tk.Tk.report_callback_exception = lambda self, exc, val, tb: exception_hook(logger, exc, val, tb)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        ui = UserInterface(root)

        root.mainloop()
    except exception as e:
        print(str(e))
        input('test')
