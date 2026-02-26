from configparser import ConfigParser


config = ConfigParser()
config.read('config.ini')

APIconfig = config['API']

LINK = APIconfig['LINK']