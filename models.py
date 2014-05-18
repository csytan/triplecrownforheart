import datetime
import uuid

from google.appengine.ext import ndb


class Settings(ndb.Model):
    admin_token = ndb.StringProperty()
    welcome_email = ndb.TextProperty()
    registration_open = ndb.BooleanProperty(default=True)
    cookie_secret = ndb.StringProperty(indexed=False)

    @classmethod
    def get_settings(cls):
        return cls.get_or_insert('settings',
            admin_token=str(uuid.uuid4()).replace('-', ''),
            cookie_secret=str(uuid.uuid4()))


class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    phone = ndb.StringProperty(indexed=False)
    emergency_contact = ndb.StringProperty(indexed=False)
    emergency_contact_phone = ndb.StringProperty(indexed=False)
    guardian = ndb.StringProperty(indexed=False)
    birth_date = ndb.StringProperty(indexed=False)
    birth_date2 = ndb.DateProperty()
    experience = ndb.StringProperty(indexed=False, choices=['new', 'intermediate', 'expert'])
    club_id = ndb.StringProperty(indexed=False)
    prev_events = ndb.StringProperty(indexed=False)
    weekly_activity = ndb.IntegerProperty(indexed=False)
    health_conditions = ndb.StringProperty(indexed=False)
    mountains = ndb.StringProperty(indexed=False, choices=['all', 'cypress', 'seymour', 'grouse'])
    street = ndb.StringProperty(indexed=False)
    city = ndb.StringProperty(indexed=False)
    province = ndb.StringProperty(indexed=False)
    postal_code = ndb.StringProperty(indexed=False)
    paid = ndb.BooleanProperty(default=False)
    paypal_txn_id = ndb.StringProperty()
    registration_type = ndb.StringProperty(indexed=False, default='adult', choices=['adult', 'student', 'senior'])

    order_jersey = ndb.BooleanProperty(indexed=False, default=False)
    gender = ndb.StringProperty(indexed=False, choices=['male', 'female'])
    jersey_size = ndb.StringProperty(indexed=False, choices=['XS', 'S', 'M', 'L', 'XL', 'XXL'])

    title = ndb.StringProperty()
    raised = ndb.IntegerProperty(default=0)
    goal = ndb.IntegerProperty(default=200)
    n_donations = ndb.IntegerProperty(default=0)
    quote = ndb.TextProperty()
    edit_token = ndb.StringProperty()

    _this_year = datetime.datetime(year=datetime.datetime.now().year, month=1, day=1)

    @classmethod
    def fetch_users(cls, sort=None, paid=False):
        users = cls.query(cls.created > cls._this_year).order(cls.created).fetch()
        if sort == 'raised':
            users.sort(key=lambda u: u.raised, reverse=True)
    	return users

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
        self.edit_token = str(uuid.uuid4()).replace('-', '')

    def registration_cost(self):
        if self.registration_type == 'adult':
            cost = 60
        elif self.registration_type == 'student':
            cost = 50
        else:
            cost = 40
        if self.order_jersey:
            cost += 70
        return cost

    def donations(self):
        return Donation.query(Donation.user == self.key).fetch(1000)

    def update_raised(self):
        donations = self.donations()
        self.n_donations = len(donations)
        self.raised = 0
        for donation in donations:
            self.raised += donation.amount


class Donation(ndb.Model):
    user = ndb.KeyProperty()
    donor_name = ndb.StringProperty(indexed=False)
    donor_email = ndb.StringProperty()
    donor_comment = ndb.TextProperty()
    amount = ndb.IntegerProperty(default=0)
    status = ndb.StringProperty(indexed=False)
    data = ndb.TextProperty()


