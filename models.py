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
    def slug(self):
    	return ''.join(s for s in self.name if s.isalnum()).lower()

    def set_edit_token(self):
        self.edit_token = str(uuid.uuid4()).replace('-', '')

    def donations(self):
        return Donation.query(Donation.user == self.key).fetch(1000)


class Donation(ndb.Model):
    user = ndb.KeyProperty()
    donor_name = ndb.StringProperty()
    donor_email = ndb.StringProperty()
    donor_comment = ndb.StringProperty()
    amount = ndb.IntegerProperty(default=0)
    gross = ndb.IntegerProperty(default=0, indexed=False)
    status = ndb.StringProperty(indexed=False)
    data = ndb.TextProperty()


