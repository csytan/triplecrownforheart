import uuid

from google.appengine.api import mail
from google.appengine.ext import ndb



class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    phone = ndb.StringProperty(indexed=False)
    emergency_contact = ndb.StringProperty(indexed=False)
    emergency_contact_phone = ndb.StringProperty(indexed=False)
    guardian = ndb.StringProperty(indexed=False)
    birth_date = ndb.DateProperty()
    experience = ndb.StringProperty(indexed=False, choices=['new', 'intermediate', 'expert'])
    club_id = ndb.StringProperty(indexed=False)
    prev_events = ndb.StringProperty(indexed=False)
    weekly_activity = ndb.IntegerProperty(indexed=False)
    health_conditions = ndb.StringProperty(indexed=False)
    allergies = ndb.StringProperty(indexed=False)
    medication = ndb.StringProperty(indexed=False)
    medical_allergies = ndb.StringProperty(indexed=False)
    mountains = ndb.StringProperty(indexed=False, choices=['all', 'cypress', 'seymour', 'grouse'])
    address = ndb.StringProperty(indexed=False)
    city = ndb.StringProperty(indexed=False)
    province = ndb.StringProperty(indexed=False)
    postal_code = ndb.StringProperty(indexed=False)
    paid = ndb.BooleanProperty(default=False)
    paypal_txn_id = ndb.StringProperty()
    registration_type = ndb.StringProperty(indexed=False, choices=['adult', 'youth', 'senior'])

    title = ndb.StringProperty()
    raised = ndb.IntegerProperty(default=0)
    goal = ndb.IntegerProperty(default=200)
    n_donations = ndb.IntegerProperty(default=0)
    quote = ndb.TextProperty()
    edit_token = ndb.StringProperty()

    @classmethod
    def users_by_raised(cls):
    	return cls.query().order(-cls.raised).fetch(1000)

    @classmethod
    def users_by_name(cls):
        return cls.query().order(cls.name).fetch(1000)

    @property
    def href(self):
        slug = ''
        for s in self.name:
            if s == ' ':
                slug += '_'
            elif s.isalnum():
                slug += s.lower()
        return '/' + str(self.key.id()) + '/' + slug

    def set_edit_token(self):
        if not self.edit_token:
            self.edit_token = str(uuid.uuid4()).replace('-', '')

    def donations(self):
        return Donation.query(Donation.user == self.key).fetch(1000)

    def update_raised(self):
        donations = self.donations()
        self.n_donations = len(donations)
        self.raised = 0
        for donation in donations:
            self.raised += donation.amount

    def send_email(self):
        template = WelcomeEmail.get_by_id('welcome_email')
        donation_link = 'http://donate.triplecrownforheart.com' + self.href
        email = template.text.format(
            donation_link=donation_link,
            edit_link=donation_link + '/edit?token=' + self.edit_token)
        mail.send_mail(sender='TripleCrownForHeart <triplecrownforheart@gmail.com>',
            to=self.email,
            subject='Welcome to Triple Crown for Heart',
            body=email)


class Donation(ndb.Model):
    user = ndb.KeyProperty()
    donor_name = ndb.StringProperty(indexed=False)
    donor_email = ndb.StringProperty()
    donor_comment = ndb.TextProperty()
    amount = ndb.IntegerProperty(default=0)
    status = ndb.StringProperty(indexed=False)
    data = ndb.TextProperty()


class WelcomeEmail(ndb.Model):
    text = ndb.TextProperty()


