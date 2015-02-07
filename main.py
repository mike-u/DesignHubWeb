import jinja2
import webapp2
import os
import datetime
import gcal_parse as CalParse

JINJA_ENVIRON = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)
    ), extensions=['jinja2.ext.autoescape'],
    autoescape=True
)
XML_FEED = "https://www.google.com/calendar/feeds/appjs0omhqdrjt9o1ilvicg3f8%40group.calendar.google.com/public/basic"
cal = CalParse.CalendarParser(xml_url=XML_FEED)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRON.get_template('index.html')
        self.response.write(template.render())

app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
