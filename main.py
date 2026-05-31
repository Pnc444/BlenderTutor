from config import load_config
from gui import App

if __name__ == "__main__":
    config = load_config()
    app = App(config)
    app.mainloop()