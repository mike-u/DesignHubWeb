import jinja2
import webapp2
import os
import datetime
import gcal_parse as GCal_Parse
import logging

from google.appengine.ext import ndb

JINJA_ENVIRON = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)
    ), extensions=['jinja2.ext.autoescape'],
    autoescape=True
)

# For parsing the DESIGNhub Google Calendar
XML_FEED = "https://www.google.com/calendar/feeds/appjs0omhqdrjt9o1ilvicg3f8%40group.calendar.google.com/public/basic"
cal = GCal_Parse.CalendarParser(xml_url=XML_FEED)
LANDING_EVENT_NUM = 4

SLACK_DB = 'slack_db'


def slack_db_key(name=SLACK_DB):
    return ndb.Key('Slack', name)


def reformat_dates(all_events):
    now = datetime.datetime.now()
    disp_events = []

    formatting = '%Y-%m-%d %H:%M:%S'
    desire = '%a %b %d, %I:%M %p'

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


class SlackDB(ndb.Model):
    user = ndb.StringProperty()
    text = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


class SlackHandler(webapp2.RequestHandler):
    def post(self):
        logging.debug(self.request.get('token'))
        logging.debug(self.request.get('text'))

        slacks = SlackDB(parent=slack_db_key(SLACK_DB))

        slacks.text = self.request.get('text')
        slacks.user = self.request.get('user_name')

        self.response.write("Message received from "
                            + self.request.get('user_name') + ": "
                            + self.request.get('text'))

        slacks.put()


class MainHandler(webapp2.RequestHandler):
    def get(self):

        slack_query = SlackDB.query(
            ancestor=slack_db_key(SLACK_DB)
        ).order(-SlackDB.date)

        slacks = slack_query.fetch(1)

        cal.parse_calendar(force_list=True)
        call_list = cal.sort_by_oldest()

        try:
            dispevents = reformat_dates(call_list)
            template_values = {
                "events": dispevents[0:LANDING_EVENT_NUM],
                "slack": slacks[0]
            }
        except IndexError:
            # Don't ever do this in real life...
            dispevents = reformat_dates(call_list)
            slacks = SlackDB(parent=slack_db_key(SLACK_DB))

            slacks.text = 'something broke'
            slacks.user = 'Oh snap'

            slacks.put()
            template_values = {
                "events": dispevents[0:LANDING_EVENT_NUM],
                "slack": slacks[0]
            }

        template = JINJA_ENVIRON.get_template('index.html')
        self.response.write(template.render(template_values))


class CalendarHandler(webapp2.RequestHandler):
    def get(self):
        cal.parse_calendar(force_list=True)
        callist = cal.sort_by_oldest()

        dispevents = reformat_dates(callist)

        template_values = {
            "events": dispevents
        }

        template = JINJA_ENVIRON.get_template('calendar.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
                                  ('/', MainHandler),
                                  ('/slackpost', SlackHandler),
                                  ('/calendar', CalendarHandler)
                              ], debug=True)
