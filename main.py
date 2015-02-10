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


class MainHandler(webapp2.RequestHandler):
    def get(self):
        cal.parse_calendar(force_list=True)
        callist = cal.sort_by_oldest()
        now = datetime.datetime.now()
        dispevents = []

        for event in callist:
            if event.start_time > now:
                dispevents.append(event)

        for showing in dispevents:
            if showing.start_time.hour is 00:
                showing.start_time = 'TBD'

        template_values = {
            "events": dispevents[0:LANDING_EVENT_NUM]
        }

        template = JINJA_ENVIRON.get_template('index.html')
        self.response.write(template.render(template_values))


class CalendarHandler(webapp2.RequestHandler):
    def get(self):
        cal.parse_calendar(force_list=True)
        callist = cal.sort_by_oldest()
        now = datetime.datetime.now()
        dispevents = []

        for event in callist:
            if event.start_time > now:
                dispevents.append(event)

        for showing in dispevents:
            if showing.start_time.hour is 00:
                showing.start_time = 'TBD'

        template_values = {
            "events": dispevents
        }

        template = JINJA_ENVIRON.get_template('calendar.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
                                  ('/', MainHandler),
                                  ('/calendar', CalendarHandler)
                              ], debug=True)
