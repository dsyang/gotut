import datetime
import re
from flask import url_for
from mmdgot import db
from wtforms import Form, TextField, validators
from wtforms.validators import ValidationError

def e164(number):
    """
    Takes a string and tries to parse a valid phone number out of it
    Modified
    """
    number = keypad(number)
    number = re.sub(r"[^0-9+]", "", number)

    # validate intl 10
    match = re.match(r"^\+([2-9][0-9]{9})$", number)
    if match:
        return u"+{}".format(match.group(1))

    # validate US DID
    match = re.match(r"^\+?1?([2-9][0-9]{9})$", number)
    if match:
        return u"+1{}".format(match.group(1))

    # validate INTL DID
    match = re.match(r"^\+?([2-9][0-9]{7,14})$", number)
    if match:
        return u"+{}".format(match.group(1))

    # premium US DID
    match = re.match(r"^\+?1?([2-9]11)$", number)
    if match:
        return u"+1{}".format(match.group(1))

    msg = "Could not parse {} as a valid phone number".format(number)
    raise ValueError(msg)


def keypad(word):
    lt = {
        'A': '2',
        'B': '2',
        'C': '2',
        'D': '3',
        'E': '3',
        'F': '3',
        'G': '4',
        'H': '4',
        'I': '4',
        'J': '5',
        'K': '5',
        'L': '5',
        'M': '6',
        'N': '6',
        'O': '6',
        'P': '7',
        'Q': '7',
        'R': '7',
        'S': '7',
        'T': '8',
        'U': '8',
        'V': '8',
        'W': '9',
        'X': '9',
        'Y': '9',
        'Z': '9'
    }
    return u"".join([lt[i.upper()] if i.upper() in lt else i for i in word])



class Game(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    name = db.StringField(max_length=255, required=True)
    slug = db.StringField(max_length=255, required=True)
    numbers = db.ListField(db.EmbeddedDocumentField('Number'))
    last_recording = db.StringField(max_length=255)
    starting_text = db.StringField(max_length=255)

    def get_absolute_url(self):
        return url_for('game', kwargs={'slug': self.slug})

    def __unicode__(self):
        return self.name

    meta = {
        'indexes': ['-created_at', 'slug'],
        'ordering': ['-created_at']
    }


class Number(db.EmbeddedDocument):
    number = db.StringField(required=True)
    confirmed = db.BooleanField(default=False)
    recording = db.URLField()
    recording_text = db.StringField()
    first = db.BooleanField(default=False)


class NewGameForm(Form):
    game_name = TextField(u'Game Name', validators=[validators.required()])
    phone_numbers  = TextField(u'Phone Numbers')

    def validate_phone_numbers(form, field):
        numbers = [n.strip() for n in field.data.split(',')]
        if len(numbers) < 2:
            raise ValidationError("You must enter at least two numbers!")
        else:
            for n in numbers:
                try:
                    e164(n)
                except ValueError:
                    raise ValidationError("The phone number {} was unable to "
                                          "be parsed, try it without parens "
                                          "or dashes".format(n))
