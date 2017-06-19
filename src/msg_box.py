import tkinter as tk
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