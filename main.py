#!/usr/bin/env python
import os

from google.appengine.ext.webapp.util import run_wsgi_app

import tornado.wsgi
import tornado.web


class Index(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class User(tornado.web.RequestHandler):
	def get(self):
		self.render('user.html')



settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'debug': os.environ['SERVER_SOFTWARE'].startswith('Dev')
}
application = tornado.wsgi.WSGIApplication([
    (r'/', Index),
    (r'/stewart', User)
], **settings)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
