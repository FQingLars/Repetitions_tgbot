from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from db_funcs import *
from datas import *
from config import LINK


app = Flask(__name__)
CORS(app, origins=[
    'https://fqinglars.github.io',
    LINK
])

@app.route('/api/schedule/list', methods=['GET'])
def api_schedule_list():
    return jsonify({"data": select_rasp()})

@app.route('/api/schedule/add', methods=['POST'])
def api_schedule_add():
    data = request.json
    insert_req(group=data['group_name'],date_time=datetime.strptime(data['datetime'], "%d.%m.%Y %H:%M"), action=data['action'])
    return jsonify({"success": True})

@app.route('/api/schedule/delete', methods=['POST'])
def api_schedule_delete():
    data = request.json
    insert_req(group=data['group_name'],date_time=datetime.strptime(data['datetime'], "%d.%m.%Y %H:%M"), action=data['action'])
    return jsonify({"success": True})

@app.route('/api/admin/check', methods=['GET'])
def api_admin_check():
    user_id = request.headers.get('X-User-Id')
    return jsonify({"is_admin": check_admin(int(user_id))})

@app.route('/api/requests/list', methods=['GET'])
def api_requests_list():
    return jsonify({"data": select_req()})

@app.route('/api/requests/<int:request_id>/approve', methods=['POST'])
def api_request_approve(request_id):
    process_req(request_id, True)
    return jsonify({"success": True})

@app.route('/api/requests/<int:request_id>/reject', methods=['POST'])
def api_request_reject(request_id):
    process_req(request_id, False)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)