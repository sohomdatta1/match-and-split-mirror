import configparser as cfp
import os

cnf_path = './replica.my.cnf'

def load_cnf():
    cnf = cfp.ConfigParser()
    cnf.read(cnf_path)
    return cnf

cnf = load_cnf()
if not os.environ.get( 'TOOLFORGE' ):
    remote = 'localhost'
    user = cnf['client']['user']
    password = cnf['client']['password']
else:
    remote = 'tools.db.svc.wikimedia.cloud'
    user = os.environ.get( 'TOOL_DATABASE_USER' )
    password = os.environ.get( 'TOOL_DATABASE_PASSWORD' )


config = {
    'host': remote,
    'username': user,
    'password': password
}