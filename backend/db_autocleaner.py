import threading
from dbfuncs import automatic_clean
import logging

def autocleaner():
    automatic_clean()
    logging.info("Старые записи были удалены из базы данных.")
    threading.Timer(1800.0, autocleaner).start()

if __name__ == '__main__':
    autocleaner()