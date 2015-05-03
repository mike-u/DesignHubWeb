__author__ = 'Ian McIntyre'

import webapp2
from google.appengine.api import channel, urlfetch
import logging
from json import dumps as jdumps
from json import load as jload
import jinja2
import os
import string
from random import SystemRandom as rand
from google.appengine.ext import ndb

HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
ERRORS = 'Error: user not online'
SLACKDB = 'Slack'

JINJA_ENVIRON = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)
    ), extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


class User(ndb.Model):
    user = ndb.StringProperty()
    token = ndb.StringProperty()


def keygen(size=25):
    genset = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(rand().choice(genset) for _ in range(size))


def import_secrets():
    """
    Contact Ian for secrets.json file. The file contains the protected URL needed to make POST requests to the channel
    of DesignHub. It is always best to keep such "secret" files, like tokens and client IDs, out of version control.
    """
    return jload(open('secrets.json'))


def get_token_by_user(him):
    db = User.query(User.user == him).fetch()
    if not db:
        return ERRORS
    else:
        return db[0].token


def send_to_slack(user, message):
    secret = import_secrets()

    payload = {"text": message,
               "username": user,
               "icon_emoji": ":ghost:"}

    r = urlfetch.fetch(url=secret['URL'],
                       payload=jdumps(payload),
                       method=urlfetch.POST,
                       headers=HEADERS)


def send_to_client(user, message, sender):
    token = get_token_by_user(user)
    if token != ERRORS:
        payload = {"response": message,
                   "from": sender}
        channel.send_message(token, jdumps(payload))
        return 'Message to ' + user + ' sent successfully: ' + message
    else:
        return token


def announce_to_slack(user, status='connected', message=None, sender=None):
    secret = import_secrets()
    if status == 'connected':
        message = user + ' has joined the chat'
    elif status == 'disconnected':
        message = user + ' has disconnected'
    elif status == 'echo' and message and sender:
        message = sender + ' replied to ' + user + ': ' + message

    payload = {"text": message,
               "username": "MC"}

    r = urlfetch.fetch(url=secret['URL'],
                       payload=jdumps(payload),
                       method=urlfetch.POST,
                       headers=HEADERS)


class ChatHandler(webapp2.RequestHandler):
    def get(self):
        token = channel.create_channel(keygen())
        template_values = {'token': token}
        template = JINJA_ENVIRON.get_template('chat.html')
        self.response.write(template.render(template_values))

    def post(self):
        pass


class SendMessageHandler(webapp2.RequestHandler):
    def post(self):
        message = self.request.get('message')
        user = self.request.get('user')
        send_to_slack(user, message)


class SlackHandler(webapp2.RequestHandler):
    def post(self):
        responder = self.request.get('user_name')
        payload = self.request.get('text')
        to_user, message = payload.split(' ', 1)
        result = send_to_client(to_user, message, responder)
        self.response.write(result)
        announce_to_slack(to_user, status='echo', message=message, sender=responder)


class ConnectionHandler(webapp2.RequestHandler):
    def post(self):
        token = self.request.get('from')
        user = "user" + keygen(size=5)
        db = User(id=token)
        db.user = user
        db.token = token
        db.put()
        announce_to_slack(user)
        to_client = {'user': user}
        channel.send_message(token, jdumps(to_client))


class DisconnectHandler(webapp2.RequestHandler):
    def post(self):
        token = self.request.get('from')
        user = ndb.Key(User, token).get()
        logging.info(user.user)
        announce_to_slack(user.user, status='disconnected')
        user.key.delete()


routes = [('/chat', ChatHandler), ('/sendmessage', SendMessageHandler),
          ('/_ah/channel/disconnected/', DisconnectHandler),
          ('/_ah/channel/connected/', ConnectionHandler),
          ('/slackchat', SlackHandler)]
app = webapp2.WSGIApplication(routes=routes, debug=True)