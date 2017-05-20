import sys
from app import app
from flask import Response
from .logic import *
import base64
import pymongo


@app.route('/')
def hello_world():
    return '''Available links:
    <ul>
    <li>/api/adduser -- adds user 'guest'</li>
    <li>/api/addpage -- adds guest's page 'brodkaR'</li>
    <li>/api/test -- tests 'brodkaR' existence and getting hash from that website</li>
    <li>/api/listusers</li>
    <li>/api/listwatched</li>
    <li>/api/restartdb</li>
    <li>/api/graphql</li>
    </ul>
    You can test the GraphQL functionality by installing Google Chrome addon : <a href="https://chrome.google.com/webstore/detail/chromeiql/fkkiamalmpiidkljmicmjfbieiclmeij"> ChromeiQL</a>. <br>
    Sample queries:
    <ul>
    <li>
    query{
        watched_pages
        {
            id
            page_name
            owner_name
            url
            authentication
        }
    }
    </li>
    <li>
    query{
        users
        {
             username
             id
        }
    }
    </li>

    <li>
     mutation{
        NewWatchedPage(url:"www.mini.pw.edu.pl",page_name:"MiNi",owner_name:"guest")
        {
            success
        }
     }
     </li>
     <li>
     mutation{
         NewUser(username:"Jack",password:"somesha1hash",email:"jack@10minutemails.com")
         {
            success
        }
     }
     </li>
    </ul>
    '''


@app.route('/qwerty')
def show_collections():
    collection = mongo.db.collection_names()
    print('Is it working?', file=sys.stderr)
    print(collection, file=sys.stderr)
    return 'Check console for output'


@app.route('/adduser')
def add_user_page():
    # Somehow get the neccessary data seen below (possibly via GraphQL)
    user = 'guest'
    password = 'swordfish'
    mail = 'guest@example.com'
    ###
    if mongo.db.users.find_one({'username': user}) is not None:
        return 'User [{}] exists in the database'.format(user)
    add_to_users(user, password, mail)
    return 'User [{}] added'.format(user)


@app.route('/addpage')
def add_watchpage_page():
    # Somehow get the neccessary data seen below (possibly via GraphQL)
    owner_name = 'guest'
    page_name = 'brodkaR'
    url = "http://www.mini.pw.edu.pl/~brodka/ASD2/Regulamin.pdf"
    authentication = base64.b64encode(bytes('s4-asd2:mini-d1234', 'utf-8')).decode('ascii')
    interval = 5
    ###
    if mongo.db.watched_pages.find_one({'owner_name': owner_name, 'page_name': page_name}) is not None:
        return 'Watchpage [{}] exists in the database'.format(page_name)
    add_to_watched_pages(owner_name, page_name, url, authentication, interval)
    return 'Webpage [{}] added'.format(page_name)


@app.route('/listusers')
def list_users_page():
    cursor = mongo.db.users.find()
    file = ""
    for doc in cursor:
        file += str(doc)
        file += '\n'
    return Response(file, mimetype='text')


@app.route('/listwatched')
def list_watched_page():
    cursor = mongo.db.watched_pages.find()
    file = ""
    for doc in cursor:
        file += str(doc)
        file += '\n'
    return Response(file, mimetype='text')


@app.route('/restartdb')
def restart_db_page():
    restart_db()
    return 'Database restarted'


@app.route('/test')
def test_page():
    return get_page_hash("brodkaR", "guest")
