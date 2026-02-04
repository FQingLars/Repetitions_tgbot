from configparser import ConfigParser


config = ConfigParser()
config.read('config.ini')

APIconfig = config['API']

APIKEY = APIconfig['APIKEY']