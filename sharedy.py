import os
import re
import cgi
import datetime
import wsgiref.handlers
import time
import hashlib
import logging

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

SECRET_KEY = "this_is_a_random_hash"

#Just trying to limit the number of "fuck you" comments
naughty = re.compile('(\s|^)(fuck|shit)(\s|$)')
url_replace = re.compile('(?P<t>http:\/\/[-\w+&@#\/%?=~_|!:,.;]*[-\w+&@#\/%=~_|])')

class Share(db.Model):
    message = db.StringProperty(multiline=True)
    time = db.DateTimeProperty(auto_now_add=True)
    ip = db.StringProperty()

    @property
    def message_html(self):
       return url_replace.sub(r'<a target="_blank" href="\g<t>">\g<t></a>', self.message)

    def is_valid(self):
        #kill the tags
        self.message =  re.sub(r'<[^>]*?>', '', self.message)
        
        if not self.message:
            return False
        if not re.sub('\s', '', self.message):
            return False
        if naughty.search(self.message):
            return False
        return True

class BaseRequestHandler(webapp.RequestHandler):
    """
    Very Simple Security.
    Makes a hash based on the IP, SECRET_KEY and timestamp
    """
    def generate_hash(self, timestamp):
        ip = self.request.remote_addr
        if not ip:
            ip = "none"
        return hashlib.md5(''.join([str(timestamp), ip, SECRET_KEY])).hexdigest()

    def generate_security(self):
        timestamp = int(time.time())
        security_hash = self.generate_hash(timestamp)
        return {'timestamp' : timestamp, 'security_hash' : security_hash}

    def validate_security(self):
        #Honeypot
        title = self.request.get('title', None)
        logging.debug("TITLE %s" % title)
        if title:
            return False

        security_hash = self.request.get('security_hash', None)
        timestamp = self.request.get('timestamp', None)
        if not security_hash or not timestamp:
            return False
        logging.debug("security_hash %s" % security_hash)
        logging.debug("timestamp %s" % timestamp)
        if security_hash != self.generate_hash(timestamp):
            return False
        #Make sure the timestamp is an int and it's not 30 minutes old
        try:
            if time.time() - int(timestamp) > (60 * 30):
                return False
        except ValueError:
            return False

        return True

class IndexPage(BaseRequestHandler):
    """Index Handler """
    def get(self):
        d = {}
        #Get the last 15 Shares
        d['shares'] = db.GqlQuery("SELECT * "
                            "FROM Share "
                            "ORDER BY time DESC LIMIT 15")

        d.update(self.generate_security())

        path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
        self.response.out.write(template.render(path,d))

class PostShare(BaseRequestHandler):
    """Post Handler """
    def post(self):
        data = simplejson.dumps({'error' :  True})

        if self.validate_security():
            share = Share()
            share.message = self.request.get('message')
            share.ip = self.request.remote_addr
            if share.is_valid():
                share.put()
                data = simplejson.dumps({'error' :  False})

        self.response.out.write(data)

application = webapp.WSGIApplication([
  ('/', IndexPage),
  ('/ajax', PostShare)
], debug=True)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
