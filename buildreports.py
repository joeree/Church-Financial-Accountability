#!/usr/bin/python
# -*- coding: utf-8 -*-

import pendulum
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.pdfbase.pdfmetrics import stringWidth as SW
import reportlab.rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

reportlab.rl_config.warnOnMissingFontGlyphs = 0


def write_balance_sheet(church_name, funds, filepath):

    # Create Page
    canvas = Canvas(filepath, pagesize=A4)
    width, height = A4  # keep for later

    # FONT
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    canvas.setFont('Arial', 18)

    # ---- Title & Headers ---- #
    header1_x = (width-SW(church_name, 'Arial', 18))/2
    canvas.drawString(header1_x, height-inch-20, church_name)

    header2_x = (width-SW('Balance Sheet Standard', 'Arial', 18))/2
    canvas.drawString(header2_x, height-inch-40, 'Balance Sheet Standard')

    date = pendulum.now().to_date_string()
    canvas.setFont('Arial', 12)
    canvas.drawString(inch, height-inch, date)

    y = 700
    # ---- TOTAL ASSETS ---- #
    # Assets
    canvas.drawString(inch, y, "ASSETS")
    canvas.drawString(width - inch * 4, y, 'Other Currency')

    total_assets = 0
    y -= 15
    for asset in funds[0]:  # for each asset
        if asset[0][:4] == '1010':
            canvas.drawString(inch + cm, y, asset[0])  # asset name
            x = SW(str(asset[1]), 'Arial', 12)
            canvas.drawString(width - inch * 2 - x, y, str(asset[1]))  # asset amount
            total_assets += asset[1]
        else:
            canvas.drawString(inch + cm, y, asset[0])  # asset name
            x = SW(str(asset[1][0]), 'Arial', 12)
            canvas.drawString(width - inch * 3.5 - x, y, str(asset[1][0]))  # asset amount (own currency)
            y -= 15

            canvas.drawString(inch + cm * 2.2, y, '{} in {}'.format(funds[0][0][0][-3:],
                                                                    asset[0][-3:]))
            x = SW(str(round(asset[1][1] * asset[1][0], 2)), 'Arial', 12)
            # asset amount (in base currency)
            canvas.drawString(width - inch * 2 - x, y, str(round(asset[1][1] * asset[1][0], 2)))
            total_assets += round(asset[1][1] * asset[1][0], 2)
        y -= 15
    canvas.line(width - inch * 3, y + 13, width - inch, y + 13)  # line
    canvas.drawString(inch+cm, y, 'Total UAH')
    ta = SW(str(total_assets), 'Arial', 12)
    canvas.drawString(width - inch - ta, y, str(total_assets))
    canvas.setLineWidth(2)  # make future lines thicker
    canvas.line(width - inch * 3, y-3, width - inch, y-3)  # line
    y -= 30
    canvas.setLineWidth(1)  # make future lines thinner
    canvas.drawString(inch, y, 'TOTAL ASSETS')
    canvas.drawString(width - inch - ta, y, str(total_assets))
    canvas.line(width - inch * 3, y-2, width - inch, y-2)  # line
    canvas.line(width - inch * 3, y-4, width - inch, y-4)  # line
    y -= 30

    # ---- LIABILITIES AND EQUITY ----
    # Liabilities
    canvas.drawString(inch, y, 'LIABILITIES & EQUITY')
    y -= 15
    canvas.drawString(inch + cm, y, 'Liability Funds')
    y -= 15
    total_liability = 0
    for liability in funds[1]:  # for each liability
        canvas.drawString(inch + cm * 2, y, liability[0])
        x = SW(str(liability[1]), 'Arial', 12)
        canvas.drawString(width - inch * 2 - x, y, str(liability[1]))
        y -= 15
        total_liability += liability[1]
    canvas.line(width - inch * 3, y + 13, width - inch, y + 13)  # line
    canvas.drawString(inch + cm, y, 'Total Liability Funds')
    tl = SW(str(total_liability), 'Arial', 12)
    canvas.drawString(width - inch - tl, y, str(total_liability))
    y -= 15

    # Equities
    canvas.drawString(inch + cm, y, 'Equity Funds')
    y -= 15
    total_equity = 0
    for equity in funds[2]:  # for each equity
        canvas.drawString(inch + cm * 2, y, equity[0])
        x = SW(str(equity[1]), 'Arial', 12)
        canvas.drawString(width - inch * 2 - x, y, str(equity[1]))
        y -= 15
        total_equity += equity[1]
    canvas.line(width - inch * 3, y + 13, width - inch, y + 13)  # line
    canvas.drawString(inch + cm, y, 'Total Equity Funds')
    teq = SW(str(total_equity), 'Arial', 12)
    canvas.drawString(width - inch - teq, y, str(total_equity))
    y -= 15

    # Revenues
    canvas.drawString(inch + cm, y, 'Net Income')
    y -= 15
    canvas.drawString(inch + cm * 2, y, 'Revenue')
    y -= 15
    total_revenue = 0
    for revenue in funds[3]:  # for each revenue
        canvas.drawString(inch + cm * 3, y, revenue[0])
        x = SW(str(revenue[1]), 'Arial', 12)
        canvas.drawString(width - inch * 2 - x, y, str(revenue[1]))
        y -= 15
        total_revenue += revenue[1]
    canvas.line(width - inch * 3, y + 13, width - inch, y + 13)  # line
    canvas.drawString(inch + cm * 2, y, 'Total Revenue')
    tr = SW(str(total_revenue), 'Arial', 12)
    canvas.drawString(width - inch - tr, y, str(total_revenue))
    y -= 15

    # Expenses
    canvas.drawString(inch + cm * 2, y, 'Expense')
    y -= 15
    total_expense = 0
    for expense in funds[4]:  # for each expense
        canvas.drawString(inch + cm * 3, y, expense[0])
        x = SW(str(expense[1]), 'Arial', 12)
        canvas.drawString(width - inch * 2 - x, y, str(expense[1]))
        y -= 15
        total_expense += expense[1]
    canvas.line(width - inch * 3, y + 13, width - inch, y + 13)  # line
    canvas.drawString(inch + cm * 2, y, 'Total Expense')
    te = SW(str(total_expense), 'Arial', 12)
    canvas.drawString(width - inch - te, y, str(total_expense))
    y -= 15

    # total net income
    canvas.drawString(inch + cm, y, 'Total Net Income')
    ne = SW(str(total_revenue + total_expense), 'Arial', 12)
    canvas.drawString(width - inch - ne, y, str(total_expense + total_revenue))
    canvas.setLineWidth(2)  # make future lines thicker
    canvas.line(width - inch * 3, y-3, width - inch, y-3)  # line
    canvas.setLineWidth(1)  # make future lines thinner
    y -= 30

    # TOTAL LIABILITIES & EQUITY
    canvas.drawString(inch, y, 'TOTAL LIABILITIES & EQUITY')
    total = total_liability + total_equity + total_revenue + total_expense
    tal = SW(str(total), 'Arial', 12)
    canvas.drawString(width - inch - tal, y, str(total))

    canvas.line(width - inch * 3, y - 2, width - inch, y - 2)  # line
    canvas.line(width - inch * 3, y - 4, width - inch, y - 4)  # line

    canvas.showPage()
    canvas.save()
