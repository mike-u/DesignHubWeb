import jinja2
import webapp2
import os

from google.appengine.ext.webapp import template


JINJA_ENVIRON = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)
    ), extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


class StaticHandler(webapp2.RequestHandler):
    def render_static_html(self, filename, **template_args):
        path = os.path.join(os.path.dirname(__file__), filename)
        self.response.write(template.render(path, template_args))


class MainHandler(StaticHandler):
    def get(self):
        self.render_static_html('construction.html')

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
