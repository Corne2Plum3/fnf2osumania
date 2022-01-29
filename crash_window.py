""" Simple tkinter called when the program encounters an error and can display a custom message (suppsed to be the error text.) """

import tkinter as tk

class Crash_window:
    """
        Class object:
            Displays a window used to show the error that happens when the program crashes.
        Arguments:
            message (str): the message to display
    """
    def __init__(self, message):
        self.message = message
        self.window = tk.Tk()

    def openWindow(self):
        """
            Class method:
                Initialize and open the window.
            Arguments:
                None.
            Return:
                Nothing
        """
        # init the window
        self.window.title(f'fnf2osumania error')  # set window title
        self.window.geometry("746x425")  # set window size
        
        # place widgets
        header = tk.Label(self.window, anchor="sw", justify="center", padx=4, pady=8, text=f'An error occured :(')
        header.grid(row=0, column=0, sticky="we")

        body_message = tk.Message(self.window, anchor="nw", justify="left", padx=4, width=742, text="The following error occured from the program while running, and eventually it crashed...\n\nIf this is the 1st time, verify your inputs and try again. If not, you should visit the GitHub for help, or open an new issue if needed, with the text error below. ")
        body_message.grid(row=1, column=0, sticky="we")

        error_text = tk.Text(self.window, padx=4, width=92, height=16)
        error_text.grid(row=2, column=0, sticky="we")
        error_text.insert("0.0", self.message)  # add the error message in the widget

        self.window.mainloop()
