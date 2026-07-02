from datetime import datetime as dt
from datetime import timezone as tz
from secrets import token_hex

import phonenumbers as ph
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from timetable.models import db
from timetable.models.timetable import (
    Events,
    Fingerprints,
    Groups,
    Missionaries,
    Person,
)

api = Blueprint("api", __name__, url_prefix="/calendar")


TOKEN_HEX = 32
# add ward here if application gets used by other wards too
KNOWN_WARDS = ("Brisbane",)


@api.route("/health")
def health():
    return jsonify({"status": "ok"})


# ------------------------------------ Missionary routes ------------------------------------
@api.route("/missionaries", methods=["GET"])
def get_missionaries():
    try:
        data = request.get_json()
        query = select(Missionaries)

        name = data.get("name")
        if name is not None:
            query = query.where(Missionaries.name.ilike(f"%{name}%"))

        allergies = data.get("allergies")  # probably represent this with boolean
        if allergies is not None:
            query = query.where(Missionaries.allergies.is_not(None))

        group_id = data.get("group")
        if group_id is not None:
            query = query.where(Missionaries.group == group_id)

        missionaries = db.session.execute(query)
        return jsonify([missionary.to_dict() for missionary in missionaries])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/missionaries/<int:id>", methods=["GET"])
def get_missionary(id):
    try:
        missionary = db.session.execute(
            select(Missionaries).where(Missionaries.id == id)
        ).scalar_one_or_none()
        if missionary is None:
            return jsonify({"error": "Missionary not found"}), 404

        return jsonify(missionary.to_dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/missionaries/", methods=["POST"])
def create_missionary():
    try:
        data = request.get_json()

        name = data.get("name")
        if name is None:
            return jsonify({"error": "Name is required"}), 400

        allergies = data.get("allergies")
        group = data.get("missionary_group")
        if group is None:
            return jsonify({"error": "Missionary group is required"}), 400

        missionary = Missionaries(name=name, allergies=allergies, group_id=group)
        db.session.add(missionary)
        db.session.commit()

        return jsonify({"message": "Missionary created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api.route("/missionaries/<int:id>", methods=["PUT"])
def update_missionary(id):
    try:
        data = request.get_json()

        name = data.get("name")
        if name is None:
            return jsonify({"error": "Name is required"}), 400

        allergies = data.get("allergies")
        group = data.get("missionary_group")
        if group is None:
            return jsonify({"error": "Missionary group is required"}), 400

        missionary = db.session.execute(
            select(Missionaries).where(Missionaries.id == id)
        ).scalar_one_or_none()
        if missionary is None:
            return jsonify({"error": "Missionary not found"}), 404

        missionary.name = name
        missionary.allergies = allergies
        missionary.group = group
        db.session.commit()

        return jsonify({"message": "Missionary updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api.route("/missionaries/<int:id>", methods=["DELETE"])
def delete_missionary(id):
    try:
        missionary = db.session.execute(
            select(Missionaries).where(Missionaries.id == id)
        ).scalar_one_or_none()
        if missionary is None:
            return jsonify({"error": "Missionary not found"}), 404

        db.session.delete(missionary)
        db.session.commit()

        return jsonify({"message": "Missionary deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ------------------------------------ Groups routes ------------------------------------
@api.route("/group", methods=["GET"])
def get_groups():
    try:
        query = select(Groups)

        type = request.args.get("missionary_type")
        if type is not None:
            if type not in ("elders", "sisters"):
                return jsonify({"error": "Invalid missionary_type"}), 400
            query = query.where(Groups.missionary_type == type)

        ward = request.args.get("ward")
        if ward is not None:
            if ward not in KNOWN_WARDS:
                return jsonify({"error": "Invalid ward"}), 400
            query = query.where(Groups.ward == ward)

        groups = db.session.execute(query).scalars().all()
        return jsonify([group.to_dict() for group in groups])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/group/<int:group_id>", methods=["GET"])
def get_group(group_id):
    try:
        group = db.session.execute(
            select(Groups).where(Groups.id == group_id)
        ).scalar_one_or_none()
        if group is None:
            return jsonify({"error": "Group not found"}), 404

        return jsonify(group.to_dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/group/<int:group_id>/events", methods=["GET"])
def get_group_events(group_id):
    try:
        query = select(Events).where(Events.missionary_group == group_id)
        events = db.session.execute(query).scalars().all()
        return jsonify([event.to_dict() for event in events])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/group", methods=["POST"])
def create_group():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Missing data"}), 400

        ward = data.get("ward")
        if ward is None:
            return jsonify({"error": "Missing ward"}), 400
        elif ward not in KNOWN_WARDS:
            return jsonify({"error": "Invalid ward"}), 400

        type = data.get("missionary_type")
        if type is None:
            return jsonify({"error": "Missing missionary type"}), 400
        elif type not in ("elders", "sisters"):
            return jsonify({"error": "Invalid missionary type"}), 400

        group = Groups(ward=ward, missionary_type=type)
        db.session.add(group)
        db.session.commit()
        return jsonify(group.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api.route("/group/<int:group_id>", methods=["PUT"])
def update_group(group_id):
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Missing data"}), 400

        group = db.session.get(Groups, group_id)
        if group is None:
            return jsonify({"error": "Group not found"}), 404

        ward = data.get("ward")
        if ward is not None:
            if ward not in KNOWN_WARDS:
                return jsonify({"error": "Invalid ward"}), 400
            group.ward = ward

        type = data.get("missionary_type")
        if type is not None:
            if type not in ("elders", "sisters"):
                return jsonify({"error": "Invalid missionary type"}), 400
            group.missionary_type = type

        db.session.commit()
        return jsonify(group.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api.route("/group/<int:group_id>", methods=["DELETE"])
def delete_group(group_id):
    try:
        group = db.session.get(Groups, group_id)
        if group is None:
            return jsonify({"error": "Group not found"}), 404

        future_events = db.session.execute(
            select(Events)
            .where(Events.missionary_group == group_id, Events.time >= dt.now(tz.utc))
            .limit(1)
        ).scalar_one_or_none()
        if future_events is not None:
            return jsonify({"error": "Group has future events"}), 409

        db.session.delete(group)
        db.session.commit()
        return jsonify({"message": "Group deleted"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ------------------------------------ Event routes ------------------------------------
@api.route("/events", methods=["GET"])
def get_events():
    try:
        query = select(Events).join(Groups, Events.missionary_group == Groups.id)

        group_id = request.args.get("group_id")
        if group_id is not None:
            query = query.where(Events.missionary_group == group_id)

        start_str = request.args.get("start")
        if start_str is not None:
            start = dt.fromisoformat(start_str).astimezone(tz.utc)
            query = query.where(Events.time >= start)

        end_str = request.args.get("end")
        if end_str is not None:
            end = dt.fromisoformat(end_str).astimezone(tz.utc)
            query = query.where(Events.time <= end)

        ward = request.args.get("ward")
        if ward is not None:
            query = query.where(Groups.ward == ward)

        events = db.session.execute(query).scalars().all()
        return jsonify([event.to_dict() for event in events])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/events/<int:id>", methods=["GET"])
def get_event(id: int):
    try:
        event = db.session.get(Events, id)
        if event is None:
            return jsonify({"error": "Event not found"}), 404

        return jsonify(event.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/events", methods=["POST"])
def create_event():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Content-Type must be application/json"}), 415

        fp_value = token_hex(TOKEN_HEX)
        fp = Fingerprints(fingerprint=fp_value)
        db.session.add(fp)
        db.session.flush()

        event_time, err = validate_time(data.get("time"))
        if err is not None:
            return err

        group_id = data.get("group_id")
        if group_id is None:
            return jsonify(
                {"error": "Event must be associated with a missionary group"}
            ), 400

        group = db.session.execute(
            select(Groups).where(Groups.id == group_id)
        ).scalar_one_or_none()
        if group is None:
            return jsonify({"error": "Invalid group_id"}), 400

        p_num = data.get("phone_num")
        last_name, f_name = data.get("l_name"), data.get("f_name")
        if p_num is None or last_name is None or f_name is None:
            return jsonify({"error": "phone_num, f_name, and l_name are required"}), 400

        p_num = validate_and_normalise_ph(p_num)
        if p_num is None:
            return jsonify({"error": "Invalid phone number"}), 400

        person = (
            db.session.execute(
                select(Person).filter_by(phone_num=p_num, l_name=last_name)
            )
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

        event = Events(
            person_id=person.id,
            fingerprint_id=fp.id,
            time=event_time,
            missionary_group=group_id,
        )

        if "description" in data:
            event.description = data.get("description")

        db.session.add(event)
        db.session.commit()

        return jsonify({**event.to_dict(), "fingerprint": fp_value}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api.route("/events/<int:id>", methods=["PUT"])
def update_event(id: int):
    try:
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

        group_id = data.get("group_id")
        if group_id is not None:
            group = db.session.execute(
                select(Groups).where(Groups.id == group_id)
            ).scalar_one_or_none()
            if group is None:
                return jsonify({"error": "Invalid group_id"}), 400

            event.missionary_group = group_id

        if "description" in data:
            event.description = data.get("description")

        db.session.commit()

        return jsonify(event.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api.route("/events/<int:id>", methods=["DELETE"])
def delete_event(id: int):
    try:
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

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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
