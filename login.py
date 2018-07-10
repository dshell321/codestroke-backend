from flask import Blueprint, request, jsonify
from functools import wraps
from extensions import mysql
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
import extensions as ext

users = Blueprint('users', __name__)

@users.route('/login/', methods=['POST'])
def user_login():
    # for testing only; TODO change to accepting pwhash instead of password
    args = ext.get_args_(['username', 'password'], request.get_json())

    query = 'select pwhash from clinicians where username = %s'
    cursor = ext.connect_()
    cursor.execute(query, (args['username'],))
    result = cursor.fetchall()

    if result:
        pwhash = result[0]['pwhash']
        if pbkdf2_sha256.verify(args['password'], pwhash):

            token = uuid4()
            query = '''update clinicians 
                       set token = %s, token_changed_time = current_timestamp 
                       where username = %s'''
            cursor.execute(query, (token, args['username']))
            mysql.connection.commit()
            
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (args['username'],))
            result = cursor.fetchall()
            user_info = result[0]
            
            return jsonify({'success': True,
                            'token': token,
                            'user_info': user_info})
        else:
            return jsonify({'success': False,
                            'debugmsg': 'Password incorrect.'})
    else:
        return jsonify({'success': False,
                        'debugmsg': 'Username incorrect'})
        
@users.route('/logout/', methods=['POST'])
def user_logout():
    args = ext.get_args_(['username', 'token'], request.get_json())
    cursor = ext.connect_()

    query = 'select token from clinicians where username = %s'
    cursor.execute(query, (args['username'],))
    result = cursor.fetchall()

    if result:
        token = result[0]['token']
        if token == args['token']:
            query = '''update clinicians 
                       set token = NULL, token_changed_time = current_timestamp 
                       where username = %s'''
            cursor.execute(query, (args['username'],))
            mysql.connection.commit()
            # TODO check result if necessary
            return jsonify({'success': True})
        else:
            return jsonify({'success': False,
                            'debugmsg': 'Wrong token.'})
    else:
        return jsonify({'success': False,
                        'debugmsg': 'Unknown username'})

def check_auth(username, token):
    cursor = ext.connect_()
    query = 'select token from clinicians where username = %s'
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    if result:
        db_token = result[0]['token']
        if db_token == token:
            return True
    return False
        
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return jsonify({'success': False,
                            'login': False,
                            'debugmsg': 'Authentication failed',})
        return f(*args, **kwargs)
    return decorated
            