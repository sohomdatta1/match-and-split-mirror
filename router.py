import os

import mwoauth
import mwoauth.flask
from flask import redirect, request, send_file, session, url_for

from app import celery as celery_app
from app import flask_app as app
from matchandsplit import match, split
from toolsdb import init_db, get_conn
init_db()

if not os.environ.get('NOTDEV'):
    from dotenv import load_dotenv
    load_dotenv()
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

inspect = celery_app.control.inspect()

@app.route('/match', methods=['POST', 'GET'])
def match_route():
    if session.get('username') is None:
        return redirect(url_for('login', referrer='/match'))
    if request.method == 'GET':
        return send_file('match.html')
    username = session['username']
    lang = request.form['lang']
    title = request.form['title']
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''INSERT INTO jobs 
                (type, lang, title, username, status)
                VALUES (%s, %s, %s, %s)''', 
                ('match', lang, title, username, 'queued'))
        conn.commit()
    match.delay(lang, title, username)
    return {'status': 'recieved'}

@app.route('/split', methods=['POST', 'GET'])
def split_route():
    if session.get('username') is None:
        return redirect(url_for('login', referrer='/split'))
    if request.method == 'GET':
        return send_file('split.html')
    lang = request.form['lang']
    title = request.form['title']
    username  = session['username']
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''INSERT INTO jobs 
                (type, lang, title, username, status)
                VALUES (%s, %s, %s, %s)''', 
                ('match', lang, title, username, 'queued'))
        conn.commit()
    split.delay(lang, title, username)
    return {'status': 'recieved'}

@app.route('/internal-status')
def all_status():
    html = open('status.html').read()
    start = 'Tasks in queue: ' + str( len(inspect.active()['worker@mas-sodium']) + len(inspect.scheduled()['worker@mas-sodium']) + len(inspect.reserved()['worker@mas-sodium']) )
    table = '<table class="wikitable"><tbody><tr><th>Task name</th><th>Language</th><th>Title</th><th>Username</th></tr>'
    rowtmpl = '<tr><td>$name</td><td>$1</td><td>$2</td><td>$3</td></tr>'
    for task in inspect.active()['worker@mas-sodium']:
        table += rowtmpl.replace('$name', task['name']).replace('$1', task['args'][0]).replace('$2', task['args'][1]).replace('$3', task['args'][2])
    for task in inspect.reserved()['worker@mas-sodium']:
        table += rowtmpl.replace('$name', task['name']).replace('$1', task['args'][0]).replace('$2', task['args'][1]).replace('$3', task['args'][2])
    for task in inspect.scheduled()['worker@mas-sodium']:
        table += rowtmpl.replace('$name', task['name']).replace('$1', task['args'][0]).replace('$2', task['args'][1]).replace('$3', task['args'][2])
    table += '</tbody></table>'
    return html + start + table

@app.route('/status/json')
def all_status_json():
    return { 'active': inspect.active()['worker@mas-sodium'], 'scheduled': inspect.scheduled()['worker@mas-sodium'], 'reserved': inspect.reserved()['worker@mas-sodium'] }

@app.route('/')
def index():
    return """
    This is experimental API for match and split. <a href="/match">/match</a> and <a href="/split">/split</a> are the two endpoints.<br>
    If the bot is taking too long, check to make sure that <a href="/status">/status</a> still has tasks in the queue. <br><br><b>You are responsible for verifying the results.</b>"""

@app.route('/login')
def login():
    """Initiate an OAuth login.
    
    Call the MediaWiki server to get request secrets and then redirect the
    user to the MediaWiki server to sign the request.
    """
    if request.args.get( 'referrer' ):
        session['referrer'] = request.args.get( 'referrer' )
    consumer_token = mwoauth.ConsumerToken(
        os.environ.get('USER_OAUTH_CONSUMER_KEY'), os.environ.get('USER_OAUTH_CONSUMER_SECRET'))
    try:
        redirect_loc, request_token = mwoauth.initiate(
            'https://meta.wikimedia.org/w/index.php', consumer_token)
    except Exception:
        app.logger.exception('mwoauth.initiate failed')
        return redirect(url_for('index'))
    else:
        session['request_token'] = dict(zip(
            request_token._fields, request_token))
        return redirect(redirect_loc)


@app.route('/mas-oauth-callback')
def oauth_callback():  
    if 'request_token' not in session:
        return redirect(url_for('index'))

    consumer_token = mwoauth.ConsumerToken(
        os.environ.get('USER_OAUTH_CONSUMER_KEY'), os.environ.get('USER_OAUTH_CONSUMER_SECRET'))

    try:
        access_token = mwoauth.complete(
            'https://meta.wikimedia.org/w/index.php',
            consumer_token,
            mwoauth.RequestToken(**session['request_token']),
            request.query_string)

        identity = mwoauth.identify(
            'https://meta.wikimedia.org/w/index.php', consumer_token, access_token)
    except Exception as _:
        app.logger.exception('OAuth authentication failed')
    
    else:
        session['access_token'] = dict(zip(
            access_token._fields, access_token))
        session['username'] = identity['username']
    
    referrer = session.get('referrer')
    session['referrer'] = None

    return redirect(referrer or '/')

@app.route('/logout')
def logout():
    """Log the user out by clearing their session."""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1238)
