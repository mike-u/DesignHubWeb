__author__ = 'Ian McIntyre'

"""
The Python webapp2 application for the DesignHub website. Commented up by Ian McIntyre on 5/17/2015. main.py is the main
entry point for all things DHub website. All web pages, excluding the chat website, are managed by this script.

Ian McIntyre
imcintyre@pittdesignhub.com
"""
import jinja2
import webapp2
import os
import datetime
#import gcal_parse as GCal_Parse
import logging
from google.appengine.ext import ndb

# Load in Jinja2 with the root directory as the source of HTML files. Escape HTML text in template variables.
JINJA_ENVIRON = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)
    ), extensions=['jinja2.ext.autoescape'],
    autoescape=True
)

# For parsing the DESIGNhub Google Calendar
#XML_FEED = "https://www.google.com/calendar/feeds/appjs0omhqdrjt9o1ilvicg3f8%40group.calendar.google.com/public/basic"
#cal = GCal_Parse.CalendarParser(xml_url=XML_FEED)
#LANDING_EVENT_NUM = 4

# The ancestor database name from which all child database entries follow
SLACK_DB = 'slack_db'


def slack_db_key(name=SLACK_DB):
    """
    Get the ancestor key for the datastore entities of Slack messages posted on the home page.
    :param name: the datastore ancestor ID (defaults to SLACK_DB)
    :return: the key of the datastore ancestor from which Slack messages child
    """
    return ndb.Key('Slack', name)

'''
def reformat_dates(all_events):
    """
    Modify the dates from the Google Calendar parser to something more readable by a human. Changes the formatting
    defined by formatting to desire. If the event is set as an all-day event, put the event as TBD. If the event has
    passed, don't display it.
    :param all_events: the events for date and time formatting
    :return: the events with human-readable date-time formatting
    """
    now = datetime.datetime.now()
    disp_events = []

    for event in all_events:
        if event.start_time > now:
            disp_events.append(event)

    for showing in disp_events:
        if showing.start_time.hour is 00:
                showing.start_time = 'TBD'
        else:
            tmp = datetime.datetime.strptime(
                str(showing.start_time), formatting
            )
            showing.start_time = tmp.strftime(desire)

    return disp_events
'''

class SlackDB(ndb.Model):
    '''
    A model for a Slack message database. Entities stored in the SlackDB database are posted on the home page with the
    most recent message first. The poster of the user is stored in user; the message for display in text. The date is
    automatically added for each entity and are indexed as such.
    '''
    user = ndb.StringProperty()
    text = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


class SlackHandler(webapp2.RequestHandler):
    """
    SlackHandler manages the storing of Slack message for display on the home page. The handler receives POST requests
    from Slack containing the user name and message of the poster. The handler echos the message back to Slack if
    successful.
    """
    def post(self):

        slacks = SlackDB(parent=slack_db_key(SLACK_DB))

        slacks.text = self.request.get('text')
        slacks.user = self.request.get('user_name')

        self.response.write("Message received from "
                            + self.request.get('user_name') + ": "
                            + self.request.get('text'))

        slacks.put()


class MainHandler(webapp2.RequestHandler):
    """
    MainHandler displays the home page. It reads the Slack message database to retrieve the most recent message sent
    from a Slack user for display on the webpage. It also parses the DHub Google Calendar to display the
    LANDING_EVENT_NUM nearest events. The data is put into template_values for parsing using JINJA2.
    """
    def get(self):

        slack_query = SlackDB.query(
            ancestor=slack_db_key(SLACK_DB)
        ).order(-SlackDB.date)

        slacks = slack_query.fetch(1)

        try:
            #dispevents = reformat_dates(call_list)
            template_values = {
                #"events": dispevents[0:LANDING_EVENT_NUM],
                "slack": slacks[0]
            }
        except IndexError:
            # Don't ever do this in real life...
            #dispevents = reformat_dates(call_list)
            slacks = SlackDB(parent=slack_db_key(SLACK_DB))

            slacks.text = 'something broke'
            slacks.user = 'Oh snap'

            slacks.put()
            template_values = {
                #"events": dispevents[0:LANDING_EVENT_NUM],
                "slack": slacks[0]
            }

        template = JINJA_ENVIRON.get_template('index.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/slackpost', SlackHandler),
    #('/calendar', CalendarHandler)
], debug=True)
