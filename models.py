import uuid

from google.appengine.ext import ndb


class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty()
    raised = ndb.IntegerProperty(default=0)
    goal = ndb.IntegerProperty(default=20)
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
        self.edit_token = str(uuid.uuid4()).replace('-', '')

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


