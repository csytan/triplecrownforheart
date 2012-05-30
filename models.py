from google.appengine.ext import ndb


class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty()
    raised = ndb.IntegerProperty(default=0)
    goal = ndb.IntegerProperty(default=20)
    n_donations = ndb.IntegerProperty(default=0)
    quote = ndb.TextProperty()

    @classmethod
    def users_by_raised(cls):
    	return cls.query().order(-cls.raised).fetch(1000)

    @classmethod
    def users_by_name(cls):
        return cls.query().order(cls.name).fetch(1000)

    @property
    def slug(self):
    	return ''.join(s for s in self.name if s.isalnum()).lower()


class Donation(ndb.Model):
    from_name = ndb.StringProperty()
    from_email = ndb.StringProperty()
    from_comment = ndb.StringProperty()
    gross = ndb.IntegerProperty(default=0, indexed=False)
    fee = ndb.IntegerProperty(default=0, indexed=False)
    status = ndb.StringProperty(indexed=False)
    data = ndb.TextProperty()

