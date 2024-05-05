from flask import request, send_file
from app import flask_app as app
from matchandsplit import match, split
from app import celery as celery_app

inspect = celery_app.control.inspect()

@app.route('/match', methods=['POST', 'GET'])
def match_route():
    if request.method == 'GET':
        return send_file('match.html')
    lang = request.form['lang']
    title = request.form['title']
    username = request.form['username']
    match.delay(lang, title, username)
    return {'status': 'recieved'}

@app.route('/split', methods=['POST', 'GET'])
def split_route():
    if request.method == 'GET':
        return send_file('split.html')
    lang = request.form['lang']
    title = request.form['title']
    username = request.form['username']
    split.delay(lang, title, username)
    return {'status': 'recieved'}

@app.route('/status')
def all_status():
    html = open('status.html').read()
    start = 'Tasks in queue: ' + str( len(inspect.active()['worker@mas-sodium']) + len(inspect.scheduled()['worker@mas-sodium']) + len(inspect.reserved()['worker@mas-sodium']) )
    table = '<table class="wikitable"><tbody><tr><th>Task name</th><th>Language</th><th>Title</th><th>Username</th></tr>'
    rowtmpl = '<tr><td>$name</td><td>$1</td><td>$2</td><td>$3</td></tr>'
    for task in inspect.active()['worker@mas-sodium']:
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1238)
