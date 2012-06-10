from flask import Blueprint, request, redirect, render_template, url_for
from flask.views import MethodView
from mmdgot.models import Game, Number
from flaskext.mongoengine.wtf import model_form
from twilio import twiml, rest
from mmdgot import app


def random_sentence():
    return "Again comes the fire spout."


count = 0
def get_next_number(g):
    global count
    if count == 0:
        count += 1
        return g.numbers[1]
    else:
        return None

def get_last_recording(g):
    return g.numbers[0].recording

def get_final_recording(g):
    return g.numbers[1].recording

URL_ROOT = 'http://4p3i.localtunnel.com'
TWILIO_NUMBER = '+16464807209'
client = rest.TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'],
                               app.config['TWILIO_AUTH_TOKEN'])

game_blueprint = Blueprint('game', __name__)


@game_blueprint.route('/game/<slug>/start', methods=['GET', 'POST'])
def start(slug):
    g = Game.objects.get()
    client.calls.create(to=g.numbers[0].number, from_=TWILIO_NUMBER,
                        url=URL_ROOT+url_for('.first_call'),
                        status_callback=URL_ROOT+url_for('.next_call'))
    return slug


@game_blueprint.route('/game/begin', methods=['GET', 'POST'])
def first_call():
    g = Game.objects.get()
    for n in g.numbers:
        if n.number == request.values.get('From'):
            n.started = True
            g.save()
            break
    r = twiml.Response()
    r.say("This is a game of telephone named {} ."
          "Press one to hear the phrase:".format(g.name))
    with r.gather(finishOnKey=1):
        r.say(random_sentence())
        r.say("Recording your voice will begin in 2 seconds,"
              "press pound to end recording")
        r.pause(length=1)
        r.record(action=url_for('.update_record'), finishOnKey='*',
                 maxLength="30", timeout="30")
    return str(r)

@game_blueprint.route('/game/record', methods=['GET', 'POST'])
def update_record():
    print "at update record: "
    g = Game.objects.get()
    r = twiml.Response()
    for n in g.numbers:
        print "n.number: {} \t req: {}".format(n.number, request.values.get('To'))
        if n.number == request.values.get('To'):
            n.recording = request.values.get('RecordingUrl')
            g.save()
            r.say("Your recording has been saved.")
            break
    return str(r)

@game_blueprint.route('/game/next', methods=['GET', 'POST'])
def next_call():
    g = Game.objects.get()
    n = get_next_number(g)
    if n:
        client.calls.create(to=n.number, from_=TWILIO_NUMBER,
                            url=URL_ROOT+url_for('.recursive_call'),
                            status_callback=URL_ROOT+url_for('.next_call'))
    else:
        start_num = '+17344081407'
        client.calls.create(to=start_num, from_=TWILIO_NUMBER,
                            url=URL_ROOT+url_for('.end_game'),
                            status_callback=URL_ROOT+url_for('.end_broadcast'))
    return "Complete"

@game_blueprint.route('/game/recur', methods=['GET', 'POST'])
def recursive_call():
    g = Game.objects.get()
    r = twiml.Response()
    r.say("This is a game of telephone named {} ."
          "Press one to hear the phrase:".format(g.name))
    with r.gather(finishOnKey=1):
        r.play(get_last_recording(g))
        r.say("Recording your voice will begin in 2 seconds,"
              "press pound to end recording")
        r.pause(length=2)
        r.record(action=url_for('.update_record'), finishOnKey='*',
                 maxLength="30", timeout="2")
        r.say("Your recorded phrase will now be sent to the next number.")
    return str(r)




@game_blueprint.route('/game/end', methods=['GET', 'POST'])
def end_game():
    g = Game.objects.get()
    r = twiml.Response()
    r.say("The game of telephone named {} has completed,"
          "The final phrase recorded was:".format(g.name))
    r.play(get_final_recording(g))
    r.say("a text message with a summary link will be sent to all participants."
          "Thank you for playing!")
    r.hangup()
    return str(r)

@game_blueprint.route('/game/broadcast', methods=['GET', 'POST'])
def end_broadcast():
    g = Game.objects.get()
    url = URL_ROOT+url_for('.summary')
    body = "Check out everyone's recording of {} " \
           "by visiting {}".format(g.name, url)
    for n in g.numbers:
        client.sms.messages.create(to=n.number, from_=TWILIO_NUMBER, body=body)
    return "Completed broadcast"

@game_blueprint.route('/game/summary', methods=['GET', 'POST'])
def summary():
    return "SUMMARY"



# @app.route('/game/new', methods=['GET', 'POST'])
# def new_game():
#     '''
#     Allows one to create a new game and add phone numbers
#     '''
#     if request.method.upper() == 'GET':
#         form = NewGameForm(request.form)
#         return render_template('game/new', form=form)
#     elif request.method.upper() == "POST":
#         form = request.get('form')
#         if form.validate():
#             numbers = form['numbers']
#             for num in numbers:
#                 number =