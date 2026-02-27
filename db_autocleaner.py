import threading
from db_funcs import automatic_clean

def autocleaner():
    automatic_clean()
    threading.Timer(1800.0, autocleaner).start()

if __name__ == '__main__':
    autocleaner()