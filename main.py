import datetime
import json
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import tornado.wsgi
import tornado.web

import models


class BaseHandler(tornado.web.RequestHandler):
    def head(self, *args, **kwargs):
        self.get(*args, **kwargs)
        self.request.body = ''


class Index(BaseHandler):
    def get(self):
        self.render('index.html', users=models.User.users_by_raised())


class Register(BaseHandler):
    def get(self):
        self.render('register.html')


class Admin(BaseHandler):
    def get(self):
        self.render('admin.html', users=models.User.users_by_name())


class User(BaseHandler):
    def get(self, id=None):
        user = models.User.get_by_id(int(id))
        if not user:
            raise tornado.web.HTTPError(404)
        end_date = datetime.date(year=2012, month=7, day=28)
        self.render('user.html', user=user,
            donations=user.donations(),
            format_dollars=self.format_dollars,
            days_left=(end_date - datetime.date.today()).days,
            admin=users.is_current_user_admin())

    @staticmethod
    def format_dollars(amount):
        return '${:,d}'.format(amount)


class EditUser(BaseHandler):
    def get(self, id=None):
        user = models.User.get_by_id(int(id)) if id else None
        token = self.get_argument('token', '')
        if not ((user and token == user.edit_token) or users.is_current_user_admin()):
            return self.redirect('/')
        self.render('user_edit.html', user=user, admin=users.is_current_user_admin())

    def post(self, id=None):
        if id:
            user = models.User.get_by_id(int(id))
        else:
            user = models.User()
        token = self.get_argument('token', '')
        if not (token == user.edit_token or users.is_current_user_admin()):
            return self.redirect('/')

        if self.get_argument('action', None) == 'remove':
            user.key.delete()
            return self.redirect('/admin')
        user.name = self.get_argument('name')
        user.email = self.get_argument('email', None)
        user.goal = int(self.get_argument('goal', 200))
        user.title = self.get_argument('title', '')
        user.quote = self.get_argument('quote', '')
        user.set_edit_token()
        user.put()

        if self.get_argument('send_email', None):
            user.send_email()
        self.redirect(user.href)


class WelcomeEmail(BaseHandler):
    def get(self):
        email = models.WelcomeEmail.get_or_insert('welcome_email')
        self.render('welcome_email.html', email=email)

    def post(self):
        email = models.WelcomeEmail.get_or_insert('welcome_email')
        email.text = self.get_argument('text', '')
        email.put()
        self.redirect('/welcome_email?message=updated')


class BulkAddUsers(BaseHandler):
    def get(self):
        import csv
        reader = csv.reader(open('riders.csv', 'r'), delimiter=',')
        for row in reader:
            user = models.User(
                name=row[0],
                email=row[1],
                title='Participant')
            user.set_edit_token()
            user.put()
            user.send_email()


class PayPalIPN(BaseHandler):
    def check_xsrf_cookie(self):
        """Disables XSRF token check"""

    def post(self):
        data = {}
        for arg in self.request.arguments:
            data[arg] = self.get_argument(arg)
        data['cmd'] = '_notify-validate'
        
        response = urllib.urlopen(
            'https://www.paypal.com/cgi-bin/webscr', 
            urllib.urlencode(data)).read()
        
        if response == 'VERIFIED':
            if data.get('txn_type') == 'web_accept':
                return self.web_accept(data)
        else:
            logging.error(response + ':' + str(data))
        self.write('1')
        
    def web_accept(self, data):
        if data['mc_currency'] != 'CAD' or \
            data['receiver_email'] != 'triplecrownforheart@gmail.com':
            return

        user_id = int(data['item_number'])
        user = models.User.get_by_id(user_id)
        if user:
            donation = models.Donation(
                user=user.key,
                id=data['txn_id'],
                donor_email=data['payer_email'],
                donor_name=data['first_name'] + ' ' + data['last_name'],
                donor_comment=data.get('custom', ''),
                amount=int(float(data['mc_gross'])),
                status=data['payment_status'],
                data=json.dumps(data))
            donation.put()
            user.update_raised()
            user.put()


settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'debug': os.environ['SERVER_SOFTWARE'].startswith('Dev')
}
app = tornado.wsgi.WSGIApplication([
    (r'/', Index),
    (r'/register', Register),
    (r'/admin', Admin),
    (r'/welcome_email', WelcomeEmail),
    (r'/new_user', EditUser),
    (r'/bulk_add_users', BulkAddUsers),
    (r'/(\d+)/.+/edit', EditUser),
    (r'/(\d+)/.+', User),
    (r'/paypal_ipn', PayPalIPN)
], **settings)

app = ndb.toplevel(app)


