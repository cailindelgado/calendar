from flask import Blueprint, jsonify

api = Blueprint('api', __name__, url_prefix='roster')


@api.route('/health')
def health():
    return jsonify({"status": "ok"})


@api.route('/events', methods=['GET'])
def get_events():
    pass


@api.route('/events/<int:id>', methods=['GET'])
def get_event(id):
    pass


@api.route('/events', methods=['POST'])
def create_event():
    pass


@api.route('/events/<int:id>', methods=['PUT'])
def update_event(id):
    pass


@api.route('/events/<int:id>', methods=['DELETE'])
def delete_event(id):
    pass
