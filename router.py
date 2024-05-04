from flask import request, jsonify
from app import flask_app as app
from matchandsplit import match, split

@app.route('/match', methods=['POST'])
def match_route():
    lang = request.form['lang']
    title = request.form['title']
    username = request.form['username']
    match.delay(lang, title, username)
    r = jsonify({'status': 'recieved'})
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

@app.route('/split', methods=['POST'])
def split_route():
    lang = request.form['lang']
    title = request.form['title']
    username = request.form['username']
    split.delay(lang, title, username)
    r = jsonify({'status': 'recieved'})
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

@app.route('/')
def index():
    return """This is experimental API for match and split. /match and /split are the two POST endpoints."""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1238)
