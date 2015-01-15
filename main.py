import webapp2
import os

from google.appengine.ext.webapp import template


class StaticHandler(webapp2.RequestHandler):
    def render_static_html(self, filename, **template_args):
        path = os.path.join(os.path.dirname(__file__), filename)
        self.response.write(template.render(path, template_args))


class MainHandler(StaticHandler):
    def get(self):
        self.render_static_html('index.html')


class ContactHandler(StaticHandler):
    def get(self):
        self.render_static_html('contact.html')


app = webapp2.WSGIApplication([
                                  ('/contact', ContactHandler),
                                  ('/', MainHandler)
                              ], debug=True)
