from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'whats good bitch'

@app.route('/test')
def ayy():
    return 'mask of percucets'

