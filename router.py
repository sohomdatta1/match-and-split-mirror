from flask import request
from app import flask_app as app
from matchandsplit import match, split

@app.route('/match', methods=['POST'])
def match_route():
    lang = request.form['lang']
    title = request.form['title']
    username = request.form['username']
    match.delay(lang, title, username)
    return {'status': 'recieved'}

@app.route('/split', methods=['POST'])
def split_route():
    lang = request.form['lang']
    title = request.form['title']
    username = request.form['username']
    split.delay(lang, title, username)
    return {'status': 'recieved'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1238)
