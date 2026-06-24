from eralchemy2 import render_er

import timetable.models.timetable
from timetable.models import db

render_er(db.metadata, "schema.png")
