import config, secret
from app import create_app

app = create_app([config, secret])
