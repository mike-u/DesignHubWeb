import jinja2
import webapp2
import os
import datetime
import gcal_parse as GCal_Parse

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


class MainHandler(webapp2.RequestHandler):
    def get(self):
        cal.parse_calendar(force_list=True)
        callist = cal.sort_by_oldest()

        dispevents = reformat_dates(callist)

        template_values = {
            "events": dispevents[0:LANDING_EVENT_NUM]
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
                                  ('/calendar', CalendarHandler)
                              ], debug=True)
