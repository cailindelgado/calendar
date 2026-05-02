from flask import Blueprint, jsonify, request
from timetable.models import db
from timetable.models.timetable import Events, Person, Fingerprints
from datetime import datetime as dt, timezone as tz

import uuid
import phonenumbers as ph


api = Blueprint('api', __name__, url_prefix='/calendar')


@api.route('/health')
def health():
    return jsonify({"status": "ok"})


@api.route('/events', methods=['GET'])
def get_events():
    type_filter = request.args.get('type')
    query = Events.query

    if type_filter in ('elders', 'sisters'):
        query = query.filter_by(missionary_type=type_filter)

    events = query.all()
    return jsonify([e.to_dict() for e in events])


@api.route('/events/<int:id>', methods=['GET'])
def get_event(id):
    event = db.session.get(Events, id)

    if event is None:
        return jsonify({'error': 'Event not found'}), 404

    return jsonify(event.to_dict())


@api.route('/events', methods=['POST'])
def create_event():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415

    fp_value = request.headers.get('X-Fingerprint-ID')
    check = validate_fingerprint(None, fp_value)
    if check is not None:
        return check

    event_time, err = validate_time(request.json.get('time'))
    if err is not None:
        return err

    missionary_type = request.json.get('missionary_type')
    if missionary_type not in ('elders', 'sisters'):
        return jsonify({'error': 'missionary_type must be elders or sisters'}), 400

    p_num = request.json.get('phone_num')
    last_name, f_name = request.json.get('l_name'), request.json.get('f_name')
    if p_num is None or last_name is None or f_name is None:
        return jsonify({'error': 'phone_num, f_name, and l_name are required'}), 400

    if not validate_ph(p_num):
        return jsonify({'error': 'Invalid phone number'}), 400

    person = Person.query.filter_by(phone_num=p_num, l_name=last_name).first()
    if person is None:
        person = Person(
            phone_num=p_num,
            f_name=f_name,
            l_name=last_name,
        )
        db.session.add(person)
        db.session.flush()
    else:
        person.phone_num = p_num
        person.f_name = f_name
        person.l_name = last_name

    fp = Fingerprints.query.filter_by(fingerprint=fp_value).first()
    if fp is None:
        fp = Fingerprints(fingerprint=fp_value)
        db.session.add(fp)
        db.session.flush()

    event = Events(
        person_id=person.id,
        fingerprint_id=fp.id,
        time=event_time,
        missionary_type=missionary_type,
    )

    if 'description' in request.json:
        event.description = request.json.get('description')

    db.session.add(event)
    db.session.commit()

    return jsonify(event.to_dict()), 201


@api.route('/events/<int:id>', methods=['PUT'])
def update_event(id):
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415

    event = db.session.get(Events, id)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404

    out = validate_fingerprint(event, request.headers.get('X-Fingerprint-ID'))
    if out is not None:
        return out

    event_time, err = validate_time(request.json.get('time'))
    if err is not None:
        return err
    event.time = event_time

    missionary_type = request.json.get('missionary_type')
    if missionary_type is not None:
        if missionary_type not in ('elders', 'sisters'):
            return jsonify({'error': 'missionary_type must be elders or sisters'}), 400

        event.missionary_type = missionary_type

    # NOTE: implement update for persons event

    if 'description' in request.json:
        event.description = request.json.get('description')

    db.session.commit()

    return jsonify(event.to_dict()), 200


@api.route('/events/<int:id>', methods=['DELETE'])
def delete_event(id):
    event = db.session.get(Events, id)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404

    out = validate_fingerprint(event, request.headers.get('X-Fingerprint-ID'))
    if out is not None:
        return out

    data = event.to_dict()
    db.session.delete(event)
    db.session.commit()
    return jsonify(data), 200


# NOTE: Helper functions


def validate_fingerprint(event: Events, fingerprint: str):
    """ 
    Validates that there is a fingerprint, that it is a valid uuid,
    and iff event then fingerprint matches the event fingerprint

    Returns:
    - None: If every check passes successfully
    - (tuple(json error message), error code): if any checks fail
    """

    if fingerprint is None:
        return jsonify({'error': 'Missing fingerprint'}), 400

    try:
        uuid.UUID(fingerprint)
    except ValueError:
        return jsonify({'error': 'Invalid fingerprint format'}), 400

    if event and event.fingerprint.fingerprint != fingerprint:
        return jsonify({'error': 'Unauthorised'}), 403

    return None


def validate_time(time_str: str):
    if time_str is None:
        return None, (jsonify({'error': 'time is required'}), 400)

    try:
        event_time = dt.fromisoformat(time_str)
    except ValueError:
        return None, (jsonify({'error': 'Invalid time format'}), 400)

    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=tz.utc)

    if event_time < dt.now(tz.utc):
        return None, (jsonify({'error': 'Invalid time set'}), 400)

    return event_time, None

def validate_ph(number: str):
    """
    Uses the phonenumber library to see if the given string is a 
    valid phone number or not

    Returns:
    True: iff number is a valid phone number
    False: Otherwise
    """
    try:
        return ph.is_valid_number(ph.parse(number, 'AU'))
    except ph.NumberParseException:
        return False
