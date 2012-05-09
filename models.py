from google.appengine.ext import ndb


class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty()
    raised = ndb.IntegerProperty()
    goal = ndb.IntegerProperty()
    quote = ndb.TextProperty()

    @classmethod
    def users_by_raised(cls):
    	return cls.query().order(-cls.raised).fetch(1000)


class Donation(ndb.Model):
    from_name = ndb.StringProperty()
    from_email = ndb.StringProperty()
    from_comment = ndb.StringProperty()
    gross = ndb.IntegerProperty(default=0, indexed=False)
    fee = ndb.IntegerProperty(default=0, indexed=False)
    status = ndb.StringProperty(indexed=False)
    data = ndb.TextProperty()

