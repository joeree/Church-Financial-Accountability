import tkinter as tk


class Calculator:
    def __init__(self, base, bgcolor):
        self.expression = ''
        self.equation = tk.StringVar()
        self.base = base

        self.bg_color = bgcolor

        self.start_up()

    def key(self, event):
        if event.char in '^ ( ) / 7 8 9 * 4 5 6 - 1 2 3 + 0 .':
            self.expression += event.char
            self.equation.set(self.expression)
        elif event.char == '=':
            self.equalpress()
        elif event.char == '\x7f':
            self.expression = self.expression[:-1]
            self.equation.set(self.expression)
        else:
            print(event)

    def press(self, num):
        self.expression += str(num)
        self.equation.set(self.expression)

    def equalpress(self):
        try:
            total = str(eval(self.expression))
            self.equation.set(total)
        except SyntaxError:
            total = ' error '
            self.equation.set(total)

    def clear(self):
        self.expression = ''
        self.equation.set('')

    def start_up(self):
        self.base.configure(background=self.bg_color)
        self.base.title('Calculator')

        expression_window = tk.Entry(self.base, textvariable=self.equation)
        expression_window.grid(column=0, row=0, columnspan=4, sticky='we')

        tup = [(2, 0), (2, 1), (2, 2), (2, 3),
               (3, 0), (3, 1), (3, 2), (3, 3),
               (4, 0), (4, 1), (4, 2), (4, 3),
               (5, 0), (5, 1), (5, 2), (5, 3),
               (6, 0), (6, 1)]
        buttons = []
        button_names = '^ ( ) / 7 8 9 * 4 5 6 - 1 2 3 + 0 .'
        names = button_names.split()
        for x in names:
            buttons.append(tk.Button(self.base, text=x, fg='black', highlightbackground=self.bg_color,
                                     command=lambda x=x: self.press(x), height=1, width=4))
            buttons[-1].grid(row=tup[names.index(x)][0], column=tup[names.index(x)][1])

        equal_button = tk.Button(self.base, text='=', fg='black', highlightbackground=self.bg_color,
                                 command=self.equalpress, height=1, width=4)
        equal_button.grid(column=2, row=6)

        clear_button = tk.Button(self.base, text='Clear', fg='black', highlightbackground=self.bg_color,
                                 command=self.clear, height=1, width=4)
        clear_button.grid(column=3, row=6)

        self.base.bind('<Key>', self.key)
        self.base.bind('<Return>', lambda e: self.equalpress())


if __name__ == '__main__':
    root = tk.Tk()
    c = Calculator(root, 'lightcyan2')

    root.mainloop()
