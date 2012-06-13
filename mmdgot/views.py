'''
VIEWS:

Module routes:
summary       ||@/game/<slug>/summary
*end_broadcast ||@/game/<slug>/broadcast
end_game      ||@/game/<slug>/end
update_record ||@/game/<slug>/record
*call_callback ||@/game/<slug>/<state>/call/<number>/callback/<int:rep>
*first_call    ||@/game/<slug>/begin
call_playback ||@/game/<slug>/<state>/call/<number>/playback
call_logic    ||@/game/<slug>/<state>/call/<number>
*start         ||@/game/<slug>/start
game_status   ||@/game/<slug>/status
*create_game   ||@/game/create
*make_next_call
'''

from flask import Blueprint, request, redirect, render_template, url_for
from flask.views import MethodView
from mmdgot.models import Game, Number, NewGameForm, e164
from flaskext.mongoengine.wtf import model_form
from twilio import twiml, rest
from mmdgot import app
import random


random.seed()

def random_sentence():
    sentences = ["Again comes the fire spout.",
                 'Fly fish traps aqua man',
                 'Maximum flavor cotton candy blaster',
                 'Price cannon eats onion rings',
                 'doe a dear a female dear',
                 'all your base are belong to us',
                 'make sandwich requires root access',
                 'four eight fifteen sixteen twenty-three fourty-two',
                 'red fish blue fish small fish big shark',
                 'danger will robinson danger']
    return random.choice(sentences)


def get_next_number(g):
    for n in g.numbers:
        if not n.recording:
            return n.number
    return None

def get_start_number(g):
    for n in g.numbers:
        if n.first:
            return n.number
    return None

def get_previous_recording(g):
    return g.last_recording


URL_ROOT = 'http://mmdgot.herokuapp.com'
TWILIO_NUMBER = '+16464807209'
client = rest.TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'],
                               app.config['TWILIO_AUTH_TOKEN'])

game_blueprint = Blueprint('game', __name__)



@game_blueprint.route('/game/create', methods=['GET', 'POST'])
def create_game():
    form = NewGameForm(request.form)
    if request.method.upper() == 'POST' and form.validate():
        digi=''.join([str(random.randint(0,9)) for i in xrange(4)])
        g = Game()
        g.name = form.game_name.data
        g.slug = ''.join([l.title() for l in (g.name.split(' '))])+digi
        g.starting_text = random_sentence()
        numbers = [n.strip() for n in form.phone_numbers.data.split(',')]
        for num in numbers:
            n = Number()
            n.number = e164(num)
            g.numbers.append(n)
        g.save()
        return redirect(url_for('game.first_call', slug=g.slug))
    return render_template('game_create.html', context = {'form': form})

@game_blueprint.route('/game/<slug>/status', methods=['GET', 'POST'])
def game_status(slug):

    return render_template('game_status.html', data = data)


@game_blueprint.route('/game/<slug>/<state>/call/<number>',
                      methods=['GET', 'POST'])
def call_logic(slug, state, number):
    g = Game.objects.get_or_404(slug=slug)
    r = twiml.Response()
    with r.gather(numDigits=1, action=url_for('.call_playback',
                                    slug=slug, state=state, number=number),
                  timeout=7):
        r.say("This is a game of telephone named {}."
              "Press one to hear the phrase".format(g.name))
    r.redirect(url_for('.call_logic', slug=slug, state=state, number=number))
    return str(r)


@game_blueprint.route('/game/<slug>/<state>/call/<number>/playback',
                      methods=['GET', 'POST'])
def call_playback(slug, state, number):
    g = Game.objects.get_or_404(slug=slug)
    r = twiml.Response()
    if state == 'f':
        r.say(g.starting_text)
    else:
        r.play(get_previous_recording(g))
    r.say("Recording your phrase will begin in 2 seconds."
          " Press pound when finished recording.")
    r.pause(length=1)
    r.record(action=(url_for('.update_record', slug=slug)), finishOnKey="*",
             maxLength="30", timeout="2")
    return str(r)

@game_blueprint.route('/game/<slug>/<state>/call/<number>/callback/<int:rep>',
                      methods=['GET', 'POST'])
def call_callback(slug, state, number, rep):
    g = Game.objects.get_or_404(slug=slug)
    print request.values, rep
    if bad_response(request.values.get('CallStatus')) and rep < 3:
        call_url = URL_ROOT + url_for('.call_logic', slug=slug,
                                      state=state, number=number)
        callback_url = URL_ROOT + url_for('.call_callback', slug=slug,
                                          state=state, number=number,
                                          rep=(rep+1))
        client.calls.create(to=number, from_=TWILIO_NUMBER,
                            url=call_url, status_callback=callback_url)
    else:
        if rep >= 3:
            for n in g.numbers:
                if n.number == number:
                    n.recording = URL_ROOT + url_for('no_op')
                    g.save()
                    break

        make_next_call(slug, state, number)
    return "Made next call"

@game_blueprint.route('/game/<slug>/begin', methods=['GET', 'POST'])
def first_call(slug):
    g = Game.objects.get_or_404(slug=slug)
    n = g.numbers[0]
    n.first = True
    g.save()

    call_url = URL_ROOT + url_for('.call_logic', slug=slug,
                                  state='f', number=n.number)
    callback_url = URL_ROOT + url_for('.call_callback', slug=slug,
                                      state='f', number=n.number, rep='0')

    client.calls.create(to=n.number, from_=TWILIO_NUMBER,
                        url=call_url, status_callback=callback_url)

    return "Starting game {}".format(slug)


def bad_response(s):
    if s in ['busy', 'failed', 'no-answer', 'canceled']:
        return True
    else:
        return False

def make_next_call(slug, state, number):
    g = Game.objects.get_or_404(slug=slug)
    number = get_next_number(g)
    if number:
        call_url = URL_ROOT + url_for('.call_logic', slug=slug
                                      , state='n', number=number)
        callback_url = URL_ROOT + url_for('.call_callback', slug=slug
                                          , state='n', number=number, rep=0)
        client.calls.create(to=number, from_=TWILIO_NUMBER,
                            url=call_url, status_callback=callback_url)

    else:
        start_num = get_start_number(g)
        end_url = URL_ROOT + url_for('.end_game', slug=slug)
        end_callback_url = URL_ROOT + url_for('.end_broadcast', slug=slug)
        if start_num:
            client.calls.create(to=start_num, from_=TWILIO_NUMBER,
                                url=end_url, status_callback=end_callback_url)
        else:
            return redirect(url_for('.end_broadcast', slug=slug))

    return "Complete"

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
            r.say("Your recording has been saved. Goodbye")
            break
    return str(r)


@game_blueprint.route('/game/<slug>/end',
                      methods=['GET', 'POST'])
def end_game(slug):
    g = Game.objects.get_or_404(slug=slug)
    r = twiml.Response()
    r.say("The game of telephone named {} has completed,"
          "The final phrase recorded was:".format(g.name))
    r.play(get_previous_recording(g))
    r.say("a text message with a summary link will be sent to all "
          "participants. Thank you for playing!")
    r.hangup()
    return str(r)


@game_blueprint.route('/game/<slug>/broadcast', methods=['GET', 'POST'])
def end_broadcast(slug):
    g = Game.objects.get_or_404(slug=slug)
    url = URL_ROOT + url_for('.summary', slug=slug)
    body = "Check out everyone's recording of {} " \
           "by visiting {}".format(g.name, url)
    for n in g.numbers:
        client.sms.messages.create(to=n.number, from_=TWILIO_NUMBER, body=body)
    return "Completed broadcast"


@game_blueprint.route('/game/<slug>/summary', methods=['GET', 'POST'])
def summary(slug):
    g = Game.objects.get_or_404(slug=slug)
    summary = {}
    summary['starting_text'] = g.starting_text
    summary['name'] = g.name
    summary['recordings'] = [n.recording for n in g.numbers]
    print g.numbers[0].recording
    print summary['recordings']
    summary['slug'] = g.slug
    summary['num'] = len(g.numbers)

    return render_template("game_summary.html", summary= summary)