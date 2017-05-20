import sys
from datetime import datetime
from flask_pymongo import PyMongo
from app import app, mongo
from pprint import pprint
from flask import Response
from bs4 import BeautifulSoup
import requests
import hashlib
import base64
import jwt


def add_to_users(username, password, email):
    result = mongo.db.users.find_one({'username': username})
    print(result, file=sys.stderr)
    if result is not None:
        return False
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    password = sha.hexdigest()
    record = {
        "username": username,
        "password": password,
        "email": email
    }
    print('Adding {}'.format(record), file=sys.stderr)
    mongo.db.users.insert_one(record)
    return True


def login(username, password):
    result = mongo.db.users.find_one({'username': username})
    print(result, file=sys.stderr)
    if result is None:
        return ""
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    password = sha.hexdigest()
    if password == result['password']:
        encoded = jwt.encode({'username': username}, 'secret', algorithm='HS256').decode("utf-8")
        return encoded
    return ""


def self_info(token):
    from .models import User
    decoded=jwt.decode(token, 'secret', algorithms=['HS256'])
    print(decoded, file=sys.stderr)
    result = mongo.db.users.find_one({'username': str(decoded['username'])})
    return User(
        username=result['username'],
        email=result['email']
    )


def add_to_previous_pages(watched_page_id, content):
    record = {
        "watched_page_id": watched_page_id,
        "content": content,
        "check_time": datetime.utcnow()
    }
    mongo.db.previous_pages.insert(record)


def add_to_watched_pages(owner_name, page_name, url, authentication="", interval=5):
    result = mongo.db.watched_pages.find_one({'owner_name': owner_name, 'page_name': page_name})
    if result is not None:
        return False
    authentication = base64.b64encode(bytes(authentication, 'utf-8')).decode('ascii')
    record = {
        "owner_name": owner_name,
        "page_name": page_name,
        "url": url,
        "authentication": authentication,
        "interval": interval
    }
    mongo.db.watched_pages.insert(record)
    return True


# Should work by ID in future
def delete_from_watched_pages(owner_name, page_name):
    result = mongo.db.watched_pages.find_one({'owner_name': owner_name, 'page_name': page_name})
    if result is None:
        return False
    mongo.db.watched_pages.remove({'owner_name': owner_name, 'page_name': page_name})
    return True


def restart_db():
    mongo.db.users.drop()
    mongo.db.watched_pages.drop()
    mongo.db.previous_pages.drop()
    add_to_users('guest', 'nopass', 'guest@example.com')
    add_to_users('jamesb', 'willreturn', '007@gov.uk')
    add_to_users('admin', 'admin', 'itsme@admin.com')
    add_to_watched_pages('guest', 'BEST', 'http://new.best.warszawa.pl/')
    add_to_watched_pages('guest', 'reddit', 'http://www.reddit.com/', interval=3)
    add_to_watched_pages('guest', 'Sis', 'https://www.sis.gov.uk/', interval=15)
    add_to_watched_pages('jamesb', 'MI6', 'https://www.sis.gov.uk/', interval=10)
    add_to_watched_pages('jamesb', 'Beretta', 'http://www.beretta.com', interval=60)


def get_page_hash(page_name, page_owner):
    doc = mongo.db.watched_pages.find_one({'owner_name': page_owner, 'page_name': page_name})
    if doc is not None:
        authentication = str(doc['authentication'])
        url = str(doc['url'])
        authentication = authentication
        headers = {'Authorization': 'Basic %s' % authentication}
        response = requests.get(url, headers=headers)
        print("Response status code: {}".format(response.status_code), file=sys.stderr)
        if response.status_code is not 200:
            return ""
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.text
        sha = hashlib.sha256()
        sha.update(content.encode('utf-8'))
        return sha.hexdigest()
    else:
        return ""
