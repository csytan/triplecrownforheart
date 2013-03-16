import datetime
import json
import os
import urllib

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb

import tornado.wsgi
import tornado.web

import models


class BaseHandler(tornado.web.RequestHandler):
    def head(self, *args, **kwargs):
        self.get(*args, **kwargs)
        self.request.body = ''

    def reload(self, copyargs=False, **kwargs):
        data = {}
        if copyargs:
            for arg in self.request.arguments:
                if arg not in ('_xsrf', 'password', 'password_again'):
                    data[arg] = self.get_argument(arg)
        data.update(kwargs)
        self.redirect(self.request.path + '?' + urllib.urlencode(data))

    @staticmethod
    def send_welcome_email(user):
        template = models.WelcomeEmail.get_by_id('welcome_email')
        donation_link = 'http://donate.triplecrownforheart.com' + user.href
        email = template.text.format(
            donation_link=donation_link,
            edit_link=donation_link + '/edit?token=' + user.edit_token)
        mail.send_mail(sender='TripleCrownForHeart <triplecrownforheart@gmail.com>',
            to=user.email,
            subject='Welcome to Triple Crown for Heart',
            body=email)


class Index(BaseHandler):
    def get(self):
        self.render('index.html', users=models.User.fetch_users(sort='raised'))


class Register(BaseHandler):
    def get(self):
        self.render('register.html')

    def post(self):
        birth_date = self.get_argument('birth_date')
        birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
        weekly_activity = self.get_argument('weekly_activity', None)

        if not self.get_argument('waiver', None):
            return self.reload()

        user = models.User(
            name=self.get_argument('name'),
            email=self.get_argument('email'),
            phone=self.get_argument('phone'),
            emergency_contact=self.get_argument('emergency_contact'),
            emergency_contact_phone=self.get_argument('emergency_contact_phone'),
            guardian=self.get_argument('guardian', None),
            birth_date=birth_date,
            experience=self.get_argument('experience'),
            club_id=self.get_argument('club_id', None),
            prev_events=self.get_argument('prev_events', None),
            weekly_activity=int(weekly_activity) if weekly_activity else None,
            health_conditions=self.get_argument('health_conditions', None),
            allergies=self.get_argument('allergies', None),
            medication=self.get_argument('medication', None),
            medical_allergies=self.get_argument('medical_allergies', None),
            mountains=self.get_argument('mountains', None),
            street=self.get_argument('street', None),
            city=self.get_argument('city', None),
            province=self.get_argument('province', None),
            postal_code=self.get_argument('postal_code', None),
            registration_type=self.get_argument('registration_type', None))
        user.set_edit_token()
        user.put()
        self.send_welcome_email(user)        
        self.redirect('/register/' + str(user.key.id()))


class RegisterPayment(BaseHandler):
    def get(self, id):
        user = models.User.get_by_id(int(id))
        if not user:
            raise tornado.web.HTTPError(404)
        self.render('register_payment.html', user=user)


class Admin(BaseHandler):
    def get(self):
        self.render('admin.html', users=models.User.fetch_users())


class User(BaseHandler):
    def get(self, id=None):
        user = models.User.get_by_id(int(id))
        if not user:
            raise tornado.web.HTTPError(404)
        end_date = datetime.date(year=2013, month=7, day=28)
        self.render('user.html', user=user,
            donations=user.donations(),
            format_dollars=self.format_dollars,
            days_left=(end_date - datetime.date.today()).days,
            admin=users.is_current_user_admin())

    @staticmethod
    def format_dollars(amount):
        return '${:,d}'.format(amount)


class EditUser(BaseHandler):
    def get(self, id):
        user = models.User.get_by_id(int(id))
        if not user:
            raise tornado.web.HTTPError(404)
        token = self.get_argument('token', '')
        if not ((user and token == user.edit_token) or users.is_current_user_admin()):
            return self.redirect('/')
        self.render('user_edit.html', user=user, admin=users.is_current_user_admin())

    def post(self, id):
        user = models.User.get_by_id(int(id))
        if not user:
            raise tornado.web.HTTPError(404)
        token = self.get_argument('token', '')
        if not (token == user.edit_token or users.is_current_user_admin()):
            return self.redirect('/')

        if self.get_argument('action', None) == 'remove':
            user.key.delete()
            return self.redirect('/admin')

        user.name = self.get_argument('name')
        user.email = self.get_argument('email')
        user.phone = self.get_argument('phone')
        user.goal = int(self.get_argument('goal', 200))
        user.title = self.get_argument('title', '')
        user.quote = self.get_argument('quote', '')        
        user.emergency_contact = self.get_argument('emergency_contact')
        user.emergency_contact_phone = self.get_argument('emergency_contact_phone')
        user.guardian = self.get_argument('guardian', None)
        user.experience = self.get_argument('experience')
        user.club_id = self.get_argument('club_id', None)
        user.prev_events = self.get_argument('prev_events', None)
        weekly_activity = self.get_argument('weekly_activity', None)
        user.weekly_activity = int(weekly_activity) if weekly_activity else None
        user.health_conditions = self.get_argument('health_conditions', None)
        user.allergies = self.get_argument('allergies', None)
        user.medication = self.get_argument('medication', None)
        user.medical_allergies = self.get_argument('medical_allergies', None)
        user.mountains = self.get_argument('mountains', None)
        user.put()

        if self.get_argument('send_email', None):
            self.send_welcome_email(user)
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

        action, user_id = data['item_number'].split(':')
        user = models.User.get_by_id(int(user_id))
        if not user:
            return

        if action == 'register':
            gross = float(data['mc_gross'])
            assert gross == user.registration_cost()
            user.paid = True
            user.paypal_txn_id = data['txn_id']
            user.put()
        elif action == 'donate':
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
    (r'/register/(\d+)', RegisterPayment),
    (r'/admin', Admin),
    (r'/welcome_email', WelcomeEmail),
    (r'/(\d+)/.+/edit', EditUser),
    (r'/(\d+)/.+', User),
    (r'/paypal_ipn', PayPalIPN)
], **settings)

app = ndb.toplevel(app)


