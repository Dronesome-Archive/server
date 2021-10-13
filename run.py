import logging

import config, secret
from app import create_app

logging.basicConfig(
    filename='log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s\t[%(funcName)s] %(message)s',
    datefmt='%y-%m-%d %H:%M:%S'
)
logging.getLogger().addHandler(logging.StreamHandler())  # without this, errors only go to log, not stderr
app = create_app([config, secret])
app.run(ssl_context=('/root/.ssl/namecom.crt', '/root/.ssl/namecom.key'))
