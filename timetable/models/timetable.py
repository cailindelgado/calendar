from datetime import datetime as dt, timezone as tz
from . import db

# Constants
DESCRIPTION_LENGTH = 200
NAME_LENGTH = 50
FINGERPRINT_LENGTH = 255
PHONE_NUM_LENGTH = 20
MISSIONARY_TYPE_LENGTH = 10


class Fingerprints(db.Model):
    ''' Device Fingerprint db: Fingerprints[id, person_id, fingerprint, created_at] '''
    __tablename__ = 'fingerprints'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    fingerprint = db.Column(db.String(FINGERPRINT_LENGTH), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: dt.now(tz.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'created_at': self.created_at,
        }
    
    def __repr__(self):
        return f'<Fingerprints {self.id}>'


class Person(db.Model):
    ''' Parishna People: Person[id, phone_num, f_name, m_name, l_name] '''
    __tablename__ = 'person'

    id = db.Column(db.Integer, primary_key=True) 
    phone_num = db.Column(db.String(PHONE_NUM_LENGTH), nullable=False)
    f_name = db.Column(db.String(NAME_LENGTH), nullable=False)
    m_name = db.Column(db.String(NAME_LENGTH), nullable=True)
    l_name = db.Column(db.String(NAME_LENGTH), nullable=False) # last name not expected to vary much

    def to_dict(self):
        return {
            'id': self.id,
            'phone_num': self.phone_num,
            'f_name': self.f_name,
            'm_name': self.m_name,
            'l_name': self.l_name,
        }

    def __repr__(self):
        return f'<Person {self.id}>'

class Events(db.Model):
    ''' Event's: Event[id, person_id, description, time, missionary_type] '''

    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False) # FK
    description = db.Column(db.String(DESCRIPTION_LENGTH), nullable=True)
    time = db.Column(db.DateTime, nullable=False)
    missionary_type = db.Column(db.String(MISSIONARY_TYPE_LENGTH), nullable=False)
    person = db.relationship('Person', lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'f_name': self.person.f_name,
            'l_name': self.person.l_name,
            'phone_num': self.person.phone_num,
            'description': self.description,
            'time': self.time.isoformat(),
            'missionary_type': self.missionary_type,
        }
    
    def __repr__(self):
        return f'<Events {self.id}>'