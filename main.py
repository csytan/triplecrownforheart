import datetime
import os

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


class Admin(BaseHandler):
    def get(self):
        self.render('admin.html', users=models.User.users_by_name())


class User(BaseHandler):
    def get(self, id=None):
        end_date = datetime.date(year=2012, month=7, day=28)
        self.render('user.html', user=models.User.get_by_id(int(id)),
            format_dollars=self.format_dollars,
            days_left=(end_date - datetime.date.today()).days,
            admin=users.is_current_user_admin())

    @staticmethod
    def format_dollars(amount):
        return '${:,d}'.format(amount)


class EditUser(BaseHandler):
    def get(self, id=None):
        if id:
            user = models.User.get_by_id(int(id))
        else:
            user = None
        self.render('user_edit.html', user=user)

    def post(self, id=None):
        if id:
            user = models.User.get_by_id(int(id))
        else:
            user = models.User()
        user.name = self.get_argument('name')
        user.goal = int(self.get_argument('goal', 20))
        user.quote = self.get_argument('quote', '')
        user.put()
        self.redirect('/' + str(user.key.id()) + '/' + user.slug)


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
        assert data['mc_currency'] == 'USD'
        assert data['receiver_email'] == 'account@caterpi.com'
        payment = models.Payment(
            key_name=data['txn_id'],
            txn_type=data['txn_type'],
            payer_email=data['payer_email'],
            gross=int(float(data['mc_gross']) * 100),
            fee=int(float(data.get('mc_fee', 0)) * 100),
            status=data['payment_status'],
            data=str(data))
        payment.put()
                
        if payment.status == 'Completed':
            user_id = int(data['item_number'])
            user = models.User.get_by_id(user_id)
            user.raised += payment.gross
            user.put()
            self.send_mail(
                user=user,
                subject='Payment received',
                template='email_payment_received.txt')


settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'debug': os.environ['SERVER_SOFTWARE'].startswith('Dev'),
    'cookie_secret': 'hello'
}
app = tornado.wsgi.WSGIApplication([
    (r'/', Index),
    (r'/admin', Admin),
    (r'/new_user', EditUser),
    (r'/(\d+)/.+/edit', EditUser),
    (r'/(\d+)/.+', User)
], **settings)

app = ndb.toplevel(app)


