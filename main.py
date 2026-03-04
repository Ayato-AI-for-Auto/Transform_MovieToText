import tkinter as tk
from src.app import WhisperApp


def main():
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
