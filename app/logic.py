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


def add_to_users(username, password, email):
    from .models import User
    result = mongo.db.users.find_one({'username': username})
    print(result, file=sys.stderr)
    if result is not None:
        user = User()
        return user
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    password = sha.hexdigest()
    record = {
        "username": username,
        "password": password,
        "email": email
    }

    print('Adding {}'.format(record), file=sys.stderr)
    user = User(
        username=username,
        email=email,
    )
    mongo.db.users.insert_one(record)
    return user


def add_to_previous_pages(watched_page_id, content):
    record = {
        "watched_page_id": watched_page_id,
        "content": content,
        "check_time": datetime.utcnow()
    }
    mongo.db.previous_pages.insert(record)


def add_to_watched_pages(owner_name, page_name, url, authentication="", interval=5):
    from .models import WatchedPage
    result = mongo.db.watched_pages.find_one({'owner_name': owner_name,'page_name':page_name})
    if result is not None:
        watched_page=WatchedPage()
        return watched_page
    authentication = base64.b64encode(bytes(authentication, 'utf-8')).decode('ascii')
    record = {
        "owner_name": owner_name,
        "page_name": page_name,
        "url": url,
        "authentication": authentication,
        "interval": interval
    }
    mongo.db.watched_pages.insert(record)
    watched_page = WatchedPage(
        owner_name=owner_name,
        page_name=page_name,
        url=url,
        authentication=authentication,
        interval=interval
    )
    return watched_page


# Should work by ID in future
def delete_from_watched_pages(owner_name, page_name):
    from .models import WatchedPage
    result = mongo.db.watched_pages.find_one({'owner_name': owner_name, 'page_name': page_name})
    print(result, file=sys.stderr)
    if result is None:
        watched_page = WatchedPage(
            owner_name="Record does not exist",
        )
        return watched_page
    watched_page = WatchedPage(
        owner_name=str(result['owner_name']),
        page_name=str(result['page_name']),
        url=str(result['url']),
        authentication=str(result['authentication']),
        interval=str(result['interval']),
        id=str(result['_id'])
    )
    mongo.db.watched_pages.remove({'owner_name': owner_name, 'page_name': page_name})
    return watched_page


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
            return "Something failed"
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.text
        sha = hashlib.sha256()
        sha.update(content.encode('utf-8'))
        return sha.hexdigest()
    else:
        return 'Watchpage [{}] does not exist in database'.format(page_name)
