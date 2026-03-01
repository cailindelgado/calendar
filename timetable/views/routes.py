from flask import Blueprint, jsonify, request
from timetable.models import db
from timetable.models.timetable import Events, Person, Fingerprints
from datetime import datetime as dt, timezone as tz

api = Blueprint('api', __name__, url_prefix='/calendar')


@api.route('/health')
def health():
    return jsonify({"status": "ok"})


@api.route('/events', methods=['GET'])
def get_events():
    events = Events.query.all()
    result = []
    for event in events:
        result.append(event.to_dict())
    
    return jsonify(result)


@api.route('/events/<int:id>', methods=['GET'])
def get_event(id):
    event = Events.query.get(id)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404

    return jsonify(event.to_dict())


@api.route('/events', methods=['POST'])
def create_event():
    if request.json.get('time') < dt.now(tz.utc):
        return jsonify({'error': 'Invalid time set'}), 400

    p_num = request.json.get('phone_num')
    last_name = request.json.get('l_name')
    person = Person.query.filter_by(phone_num=p_num, l_name=last_name).first()
    if person is None:
        person = Person(
            phone_num = p_num, 
            f_name = request.json.get('f_name'),
            l_name = last_name,
        )
        if 'm_name' in request.json:
            person.m_name = request.json.get('m_name')
        db.session.add(person)
        db.session.flush()

    event = Events(
        person_id = person.id,
        time = request.json.get('time'),
    )
    if 'description' in request.json:
        event.description = request.json.get('description')

    fingerprint = Fingerprints(
        person_id = person.id,
        fingerprint = request.headers.get('X-Fingerprint-ID'),
    )

    db.session.add(event)
    db.session.add(fingerprint)
    db.session.commit()

    return jsonify(event.to_dict()), 201


@api.route('/events/<int:id>', methods=['PUT'])
def update_event(id):
    # same validation check as delete, then update similarly with creating a new event
    pass


@api.route('/events/<int:id>', methods=['DELETE'])
def delete_event(id):
    event = Events.query.get(id)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404

    user_fingerprint = Fingerprints.query.get(event.fingerprint)
    if user_fingerprint is None:
        return jsonify({'error': 'Fingerprint not found'}), 404

    # get fingerprint from user
    fingerprint = request.headers.get('X-Fingerprint-ID')
    if fingerprint is None:
        return jsonify({'error': 'Missing fingerprint'}), 400

    if user_fingerprint != fingerprint:
        return jsonify({'error': 'Unauthorised'}), 403 
    
    data = event.to_dict()
    db.session.delete(event)
    db.session.commit()
    return jsonify(data), 200