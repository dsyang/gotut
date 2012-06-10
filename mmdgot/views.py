from flask import Blueprint, request, redirect, render_template, url_for
from flask.views import MethodView
from mmdgot.models import Game, Number
from flaskext.mongoengine.wtf import model_form
from twilio import twiml, rest
from mmdgot import app
import random

def random_sentence():
    sentences = ["Again comes the fire spout.",
                 'Fly fish traps aqua man',
                 'Maximum flavor cotton candy blaster',
                 'Price cannon eats onion rings',
                 'doe a dear a female dear',
                 'all your base are belong to us',
                 'make sandwich requires root access',
                 'danger will robinson danger']
    return random.choice(sentences)

def get_next_number(g):
    for n in g.numbers:
        if not n.recording:
            return n.number
    return None

def get_previous_recording(g):
    return g.last_recording

URL_ROOT = 'http://4g6j.localtunnel.com'
TWILIO_NUMBER = '+16464807209'
client = rest.TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'],
                               app.config['TWILIO_AUTH_TOKEN'])

game_blueprint = Blueprint('game', __name__)


@game_blueprint.route('/game/<slug>/start', methods=['GET', 'POST'])
def start(slug):
    g = Game.objects.get_or_404(slug=slug)
    client.calls.create(to=g.numbers[0].number, from_=TWILIO_NUMBER,
                        url=URL_ROOT+url_for('.first_call', slug=slug),
                        status_callback=URL_ROOT+url_for('.next_call',
                                                         slug=slug))
    return slug


@game_blueprint.route('/game/<slug>/begin', methods=['GET', 'POST'])
def first_call(slug):
    g = Game.objects.get_or_404(slug=slug)
    for n in g.numbers:
        if n.number == request.values.get('To'):
            n.first = True
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
        r.record(action=url_for('.update_record', slug=slug), finishOnKey='*',
                 maxLength="30", timeout="2")
    return str(r)

@game_blueprint.route('/game/<slug>/record', methods=['GET', 'POST'])
def update_record(slug):
    print "at update record: "
    g = Game.objects.get_or_404(slug=slug)
    r = twiml.Response()
    for n in g.numbers:
        print "n.number: {} \t req: {}".format(n.number,
                                               request.values.get('To'))
        if n.number == request.values.get('To'):
            n.recording = request.values.get('RecordingUrl')
            g.last_recording = request.values.get('RecordingUrl')
            g.save()
            r.say("Your recording has been saved.")
            break
    return str(r)

@game_blueprint.route('/game/<slug>/next', methods=['GET', 'POST'])
def next_call(slug):
    g = Game.objects.get_or_404(slug=slug)
    number = get_next_number(g)
    if number:
        client.calls.create(to=number, from_=TWILIO_NUMBER,
                            url=URL_ROOT+url_for('.recursive_call', slug=slug),
                            status_callback=URL_ROOT+url_for('.next_call',
                                                             slug=slug))
    else:
        start_num = '+17344081407'
        client.calls.create(to=start_num, from_=TWILIO_NUMBER,
                            url=URL_ROOT+url_for('.end_game', slug=slug),
                            status_callback=URL_ROOT+url_for('.end_broadcast',
                                                             slug=slug))
    return "Complete"

@game_blueprint.route('/game/<slug>/recur/',
                      methods=['GET', 'POST'])
def recursive_call(slug):
    g = Game.objects.get_or_404(slug=slug)
    r = twiml.Response()
    r.say("This is a game of telephone named {} ."
          "Press one to hear the phrase:".format(g.name))
    with r.gather(finishOnKey=1):
        r.play(get_previous_recording(g))
        r.say("Recording your voice will begin in 2 seconds,"
              "press pound to end recording")
        r.pause(length=2)
        r.record(action=url_for('.update_record',slug=slug), finishOnKey='*',
                 maxLength="30", timeout="2")
    return str(r)




@game_blueprint.route('/game/<slug>/end',
                      methods=['GET', 'POST'])
def end_game(slug):
    g = Game.objects.get_or_404(slug=slug)
    r = twiml.Response()
    r.say("The game of telephone named {} has completed,"
          "The final phrase recorded was:".format(g.name))
    r.play(get_previous_recording(g))
    r.say("a text message with a summary link will be sent to all participants."
          "Thank you for playing!")
    r.hangup()
    return str(r)

@game_blueprint.route('/game/<slug>/broadcast', methods=['GET', 'POST'])
def end_broadcast(slug):
    g = Game.objects.get_or_404(slug=slug)
    url = URL_ROOT+url_for('.summary', slug=slug)
    body = "Check out everyone's recording of {} " \
           "by visiting {}".format(g.name, url)
    for n in g.numbers:
        client.sms.messages.create(to=n.number, from_=TWILIO_NUMBER, body=body)
    return "Completed broadcast"

@game_blueprint.route('/game/<slug>/summary', methods=['GET', 'POST'])
def summary(slug):
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