'''
Configuration Settings
'''

''' Uncomment to configure using the file.
WARNING: Be careful not to post your account credentials on GitHub.

TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "yyyyyyyyyyyyyyyy"
TWILIO_APP_SID = "APzzzzzzzzz"
TWILIO_CALLER_ID = "+17778889999"
'''
'''

This is the coffiguration for heroku's mongodb:
MONGOLAB_URI = 'mongodb://heroku_app5033310:onqn6daqivk9' \
'sekgbivnhp64hm@ds033757.mongolab.com:33757/heroku_app5033310'

'''
# Begin Heroku configuration - configured through environment variables.
import os
PORT = os.environ.get('PORT', None)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', None)
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', None)
TWILIO_CALLER_ID = os.environ.get('TWILIO_CALLER_ID', None)
TWILIO_APP_SID = os.environ.get('TWILIO_APP_SID', None)
MONGOLAB_URI = os.environ.get('MONGOLAB_URI', None)
BITLY_LOGIN = os.environ.get('BITLY_LOGIN', None)
BITLY_API_KEY = os.environ.get('BITLY_API_KEY', None)