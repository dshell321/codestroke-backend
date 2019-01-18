""" The main app module.
This is the main app module and contains the WSGI handler.

This app also exposes routes which are registered under

"""

from flask import Flask, jsonify, request, redirect, url_for, session, flash
from flask_cors import CORS

from modules.cases import cases
from modules.case_info import case_info
from modules.admins import admins
from modules.clinicians import clinicians, requires_clinician
from modules.event_log import event_log, log_event
from modules.extensions import mysql


app = Flask(__name__)
app.config.from_pyfile('app.conf')
CORS(app)

mysql.init_app(app)

app.register_blueprint(cases)
app.register_blueprint(case_info, url_prefix='/case<info_table>')
app.register_blueprint(clinicians, url_prefix='/clinicians')
app.register_blueprint(admins, url_prefix='/admins/')
app.register_blueprint(event_log, url_prefix='/event_log')

@app.route('/')
@requires_clinician
def index(user_info):
    if ext.check_database_():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error_type': 'database'}), 500

@app.route('/version/', methods=(['GET']))
def get_version():
    version = app.config.get('VERSION')
    if version:
        return jsonify({'success': True, 'error_type': 'version', 'version': version})
    else:
        return jsonify({'success': False, 'debugmsg': 'Version not specified'}), 500


if __name__ == '__main__':
    app.run(debug = True)
