from datetime import datetime as dt
from datetime import timezone as tz
from secrets import token_hex as thex

import phonenumbers as ph
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from timetable.models import db
from timetable.models.timetable import Events, Fingerprints, Person

api = Blueprint("api", __name__, url_prefix="/calendar")


TOKEN_HEX = 32


@api.route("/health")
def health():
    return jsonify({"status": "ok"})


@api.route("/events", methods=["GET"])
def get_events():
    type_filter = request.args.get("type")
    query = select(Events)

    if type_filter in ("elders", "sisters"):
        query = query.where(Events.missionary_type == type_filter)

    events = db.session.execute(query).scalars().all()
    return jsonify([event.to_dict() for event in events])


@api.route("/events/<int:id>", methods=["GET"])
def get_event(id: int):
    event = db.session.get(Events, id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    return jsonify(event.to_dict())


@api.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    fp_value = thex(TOKEN_HEX)

    event_time, err = validate_time(data.get("time"))
    if err is not None:
        return err

    missionary_type = data.get("missionary_type")
    if missionary_type not in ("elders", "sisters"):
        return jsonify({"error": "missionary_type must be elders or sisters"}), 400

    p_num = data.get("phone_num")
    last_name, f_name = data.get("l_name"), data.get("f_name")
    if p_num is None or last_name is None or f_name is None:
        return jsonify({"error": "phone_num, f_name, and l_name are required"}), 400

    p_num = validate_and_normalise_ph(p_num)
    if p_num is None:
        return jsonify({"error": "Invalid phone number"}), 400

    person = (
        db.session.execute(select(Person).filter_by(phone_num=p_num, l_name=last_name))
        .scalars()
        .first()
    )
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

    fp = (
        db.session.execute(select(Fingerprints).filter_by(fingerprint=fp_value))
        .scalars()
        .first()
    )
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

    if "description" in data:
        event.description = data.get("description")

    db.session.add(event)
    db.session.commit()

    return jsonify({**event.to_dict(), "fingerprint": fp_value}), 201


@api.route("/events/<int:id>", methods=["PUT"])
def update_event(id: int):
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    event = db.session.get(Events, id)
    if event is None:
        return jsonify({"error": "Event not found"}), 404

    fingerprint = request.headers.get("X-Fingerprint-ID")
    if event.fingerprint.fingerprint != fingerprint:
        return jsonify({"error": "Unauthorised"}), 403

    event_time, err = validate_time(data.get("time"))
    if err is not None:
        return err
    event.time = event_time  # type: ignore[reportAttributeAccessIssue]

    missionary_type = data.get("missionary_type")
    if missionary_type is not None:
        if missionary_type not in ("elders", "sisters"):
            return jsonify({"error": "missionary_type must be elders or sisters"}), 400

        event.missionary_type = missionary_type

    if "description" in data:
        event.description = data.get("description")

    db.session.commit()

    return jsonify(event.to_dict()), 200


@api.route("/events/<int:id>", methods=["DELETE"])
def delete_event(id: int):
    event = db.session.get(Events, id)
    if event is None:
        return jsonify({"error": "Event not found"}), 404

    fingerprint = request.headers.get("X-Fingerprint-ID")
    if event.fingerprint.fingerprint != fingerprint:
        return jsonify({"error": "Unauthorised"}), 403

    data = event.to_dict()
    db.session.delete(event)
    db.session.commit()
    return jsonify(data), 200


# NOTE: Helper functions


def validate_time(time_str: str | None):
    """
    Validates the time string and returns a datetime object if valid,
    or an error message if invalid.

    Returns:
    - datetime object: If the time string is valid
    - (tuple(json error message), error code): If the time string is invalid
    """
    if time_str is None:
        return None, (jsonify({"error": "time is required"}), 400)

    try:
        event_time = dt.fromisoformat(time_str)
    except ValueError:
        return None, (jsonify({"error": "Invalid time format"}), 400)

    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=tz.utc)

    if event_time < dt.now(tz.utc):
        return None, (jsonify({"error": "Invalid time set"}), 400)

    return event_time, None


def validate_and_normalise_ph(number: str) -> str | None:
    """
    Uses the phonenumber library to see if the given string is a
    valid phone number or not, then it returns a normalised phone
    number

    Returns:
        string: If the phone number is valid and can be parsed
        None: Otherwise
    """
    try:
        num = ph.parse(number, default_region="AU")

        if not ph.is_valid_number(num):
            return None

        return ph.format_number(num, ph.PhoneNumberFormat.E164)

    except ph.NumberParseException:
        return None
