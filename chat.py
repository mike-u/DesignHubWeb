__author__ = 'Ian McIntyre'

"""
The Python webapp2 application for the DesignHub website. Commented up by Ian McIntyre on 5/17/2015. chat.py is a script
that manages the anonymous posting feature to the DH Slack channel. It requires the secrets.json file to be in the same
directory as the script. Contact Ian for a copy of the file. Elements of the script are commented below.

Ian McIntyre
imcintyre@pittdesignhub.com
"""

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
import names

# Global variables
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
ERRORS = 'Error: user not online'

# Load in Jinja2 with the root directory as the source of HTML files. Escape HTML text in template variables.
JINJA_ENVIRON = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)
    ), extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


class User(ndb.Model):
    """
    A model for an anonymous user temporary database entry. The user's randomly assigned name is stored in user, and
    the protected channel token is stored in token. The user model is temporary. It is created when an anonymous user
    connects, and the entity is destroyed when the user disconnects.
    """
    user = ndb.StringProperty()
    token = ndb.StringProperty()


def keygen(size=25):
    """
    Generate a random key of default size 25. The key is used for generating the unique channel identifier.
    """
    genset = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(rand().choice(genset) for _ in range(size))


def import_secrets():
    """
    Contact Ian for secrets.json file. The file contains the protected URL needed to make POST requests to the channel
    of DesignHub. It is always best to keep such "secret" files, like tokens and client IDs, out of version control.
    imcintyre@pittdesignhub.com
    """
    return jload(open('secrets.json'))


def get_token_by_user(him):
    """
    Find the channel token based on the anonymous user's name. If the user is connected (in the database), return the
    token to communicate with that channel. Otherwise, throw ERROR to be echoed by Slack.

    :param him: the name of the anonymous user
    :return: ERROR if the user is not connected, or the user's token (zeroth element of the fetch from the database).
    """
    db = User.query(User.user == him).fetch()
    if not db:
        return ERRORS
    else:
        return db[0].token


def send_to_slack(user, message):
    """
    Send the message of an anonymous user from the website to the Slack channel. Define the name of the anonymous user,
    the message of the anonymous user, and the ghost icon identifying the anonymous user in the Slack channel. Must be
    a POST request to the Slack server (see Slack documentation as well as the DHub inbound webhook.

    :param user: the anonymous name of the poster
    :param message: the message of the poster
    :return: None
    """
    secret = import_secrets()

    payload = {"text": message,
               "username": user,
               "icon_emoji": ":ghost:"}

    r = urlfetch.fetch(url=secret['URL'],
                       payload=jdumps(payload),
                       method=urlfetch.POST,
                       headers=HEADERS)


def send_to_client(user, message, sender):
    """
    Send a message from the Slack channel to the anonymous user on the website, provided that the user has not closed
    their browser window. Responses are generated using a /respond slash command, noting the name of the recipient, and
    finally the message. For example,

        /respond Goldwater thanks for your feedback!

    Sends the message "thanks for your feedback!" to Goldwater. The name of the sender is provided to the anonymous
    poster.

    :param user: the anonymous recipient of the response
    :param message: the message for the anonymous recipient
    :param sender: the name of the sender (their Slack ID)
    :return: an echo from the slackbot on success, otherwise the ERRORS message
    """
    token = get_token_by_user(user)
    if token != ERRORS:
        payload = {"response": message,
                   "from": sender}
        channel.send_message(token, jdumps(payload))
        return 'Message to ' + user + ' sent successfully: ' + message
    else:
        return ERRORS


def announce_to_slack(user, status='connected', message=None, sender=None):
    """
    Provides the voice of the master of ceremonies (MC). Allows the message of a Slack sender to be echoed to all others
    in the channel. The MC also announces the arrival and departure of an anonymous poster, so that Slack users do not
    try to respond to someone who has left the chat webpage.

    :param user: the anonymous user who is visiting the chat webpage
    :param status: the type of message that the MC announces. Must be either 'connected' (default), 'disconnected', or
        'echo'. status='echo' also requires the message and sender
    :param message: the message that the Slack user sent to the anonymous poster. The message is echoed back to the
        Slack team
    :param sender: the Slack sender who is responding to the anonymous poster. The sender is echoed back to the Slack
        team
    :return: None
    """
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
    """
    Manages the rendering of the chat.html webpage in the browser of a client. The channel token is injected into the
    HTML of the webpage to provide a real-time channel protocol between the client and this server. POST requests to
    the chat URL are ignored.
    """
    def get(self):
        token = channel.create_channel(keygen())
        template_values = {'token': token}
        template = JINJA_ENVIRON.get_template('chat.html')
        self.response.write(template.render(template_values))

    def post(self):
        pass


class SendMessageHandler(webapp2.RequestHandler):
    """
    Accepts POST requests that contain messages from an anonymous user on the chat website. The message and anonymous
    sender are parsed from the POST payload and relayed to the Slack channel using send_to_slack.
    """
    def post(self):
        message = self.request.get('message')
        user = self.request.get('user')
        send_to_slack(user, message)


class SlackHandler(webapp2.RequestHandler):
    """
    Handles POST requests from Slack that contain messages from the Slack channel for the specified anonymous user. The
    responder is the Slack user that answered the anonymous user. The payload is the user's message for the anonymous
    user. to_user is the anonymous recipient of the message. send_to_client performs the token lookup based on the user
    name. If there is an error, the error is echoed to the Slack team.
    """
    def post(self):
        responder = self.request.get('user_name')
        payload = self.request.get('text')
        to_user, message = payload.split(' ', 1)
        result = send_to_client(to_user, message, responder)
        self.response.write(result)
        if result != ERRORS:
            announce_to_slack(to_user, status='echo', message=message, sender=responder)


class ConnectionHandler(webapp2.RequestHandler):
    """
    ConnectionHandler manages the connection of new anonymous users via the Google Channel API. For every successful
    connection established, a user is generated with a unique token, and the pair are stored in the datastore as long as
    the user is connected. The anonymous name of the user is generated in this callback, and the user is announced to
    the Slack team by the MC.
    """
    def post(self):
        token = self.request.get('from')
        user = names.get_first_name()
        db = User(id=token)
        db.user = user
        db.token = token
        db.put()
        announce_to_slack(user)
        to_client = {'user': user}
        channel.send_message(token, jdumps(to_client))


class DisconnectHandler(webapp2.RequestHandler):
    """
    DisconnectHandler manages the connection of anonymous users via the Google Channel API. When a user leaves the chat
    webpage, the callback is issued to delete the anonymous user and token from the datastore. The MC announces that the
    user has logged off.
    """
    def post(self):
        token = self.request.get('from')
        user = ndb.Key(User, token).get()
        logging.info(user.user)
        announce_to_slack(user.user, status='disconnected')
        user.key.delete()

# Define routes for the website. GET and POST requests are made to these handlers (all defined above)
routes = [('/chat', ChatHandler), ('/sendmessage', SendMessageHandler),
          ('/_ah/channel/disconnected/', DisconnectHandler),
          ('/_ah/channel/connected/', ConnectionHandler),
          ('/slackchat', SlackHandler)]

# Start the web application
app = webapp2.WSGIApplication(routes=routes, debug=True)
