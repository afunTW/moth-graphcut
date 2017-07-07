import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno
from tkinter.messagebox import askokcancel
from tkinter.messagebox import showwarning


class MessageBox(object):

    # ask question UI
    def ask_ques(self, title='Question', string='Do you want to save?', icontype='info'):
        # icontype can be "error", "warning", "info"
        self.root = tk.Tk()
        self.center()
        self.root.withdraw()
        result = askokcancel(title, string, icon=icontype)
        self.root.destroy()
        self.root.mainloop()
        return result

    def alert(self, title='Alert', string='Please at least add one target'):
        self.root = tk.Tk()
        self.root.withdraw()
        showwarning(title, string)
        self.root.destroy()
        self.root.mainloop()

    def center(self):
        self.root.update_idletasks()
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        size = tuple(int(_) for _ in self.root.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        self.root.geometry("%dx%d+%d+%d" % (size + (x, y)))

class Instruction(object):

    def __init__(self, title='Settings'):
        super().__init__()
        self.title = title
        self.label_font = ('Helvetica', 14, 'bold')
        self.content_font = ('Helvetica', 12)
        self.__hotkey = []
        self.__action = []

    def reset(self):
        self.__hotkey = []
        self.__action = []

    def row_append(self, hotkey, description):
        self.__hotkey.append(hotkey)
        self.__action.append(description)

    def show(self):
        self.window = tk.Tk()
        self.window.title(self.title)
        self.window.resizable(0, 0)

        s = ttk.Style()
        s.configure('BLUE.TLabelframe.Label', foreground='blue', font=self.label_font)

        hotkey = ttk.LabelFrame(self.window, text='Hotkey', style='BLUE.TLabelframe')
        hotkey.grid(column=0, row=len(self.__hotkey))
        for i, k in enumerate(self.__hotkey):
            ttk.Label(hotkey, text=k, font=self.content_font).grid(column=0, row=i)

        action = ttk.LabelFrame(self.window, text='Action', style='BLUE.TLabelframe')
        action.grid(column=1, row=len(self.__action))
        for i, description in enumerate(self.__action):
            ttk.Label(action, text=description, font=self.content_font).grid(column=1, row=i, sticky=tk.W)

        self.window.mainloop()
