import jinja2
import webapp2
import os


JINJA_ENVIRON = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)
    ), extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRON.get_template('index.html')
        self.response.write(template.render())

app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
