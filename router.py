from flask import request, send_file
from app import flask_app as app
from matchandsplit import match, split

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

@app.route('/')
def index():
    return """This is experimental API for match and split. <a href="/match">/match</a> and <a href="/split">/split</a> are the two endpoints.<br><b>You are responsible for verifying the results.</b>"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1238)
