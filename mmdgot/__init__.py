import os

from flask import Flask
from flask import render_template
from flask import url_for
from flask import request

from twilio import twiml
from twilio.util import TwilioCapability

import local_settings
from flaskext.mongoengine import MongoEngine



# Declare and configure application
app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('local_settings.py')
if app.config['MONGOLAB_URI']:
    from pymongo.uri_parser import parse_uri
    params = parse_uri(app.config['MONGOLAB_URI'])
    app.config['MONGODB_DB'] = params['database']
    app.config['MONGODB_USERNAME'] = params['username']
    app.config['MONGODB_PASSWORD'] = params['password']
    app.config['MONGODB_HOST'] = params['nodelist'][0][0]
    app.config['MONGODB_PORT'] = params['nodelist'][0][1]
else:
    app.config["MONGODB_DB"] = 'tetetetelephone'


db = MongoEngine(app)

def register_blueprints():
    from mmdgot.views import game_blueprint
    app.register_blueprint(game_blueprint)

register_blueprints()


@app.route('/callbacks', methods=['GET', 'POST'])
def callback():
    return ""

# Voice Request URL
@app.route('/voice', methods=['GET', 'POST'])
def voice():
    response = twiml.Response()
    response.say("Congratulations! You deployed the Twilio Hackpack"
            " for Heroku and Flask. WORD")
    return str(response)


# SMS Request URL
@app.route('/sms', methods=['GET', 'POST'])
def sms():
    response = twiml.Response()
    response.sms("Congratulation! You deployed the Twilio Hackpack"
            " for Heroku and Flask.")
    return str(response)


# Installation success page
@app.route('/')
def index():
    params = {
        'voice_request_url': url_for('.voice', _external=True),
        'sms_request_url': url_for('.sms', _external=True),
    }
    return render_template('index.html', params=params)

# If PORT not specified by environment, assume development config.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)
