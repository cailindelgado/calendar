// ---- Config ----
const API_BASE = '/calendar';

// ---- Fingerprint ----
// A UUID stored in localStorage acts as the user's identity token.
// The server validates mutations against it.
function getFingerprint() {
  let fp = localStorage.getItem('meal_roster_fp');
  if (!fp) {
    fp = crypto.randomUUID();
    localStorage.setItem('meal_roster_fp', fp);
  }
  return fp;
}

// ---- State ----
let calendar;
let pendingDate = null;   // ISO date string clicked for signup
let activeType = 'elders';
let editingEventId = null;

function setType(type) {
  activeType = type;
  document.getElementById('toggleElders').className  = 'toggle-btn' + (type === 'elders'  ? ' active-elders'  : '');
  document.getElementById('toggleSisters').className = 'toggle-btn' + (type === 'sisters' ? ' active-sisters' : '');
  calendar.refetchEvents();
}

// ---- Helpers ----
function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2800);
}

function openModal(id) {
  document.getElementById(id).classList.add('open');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  if (id === 'signupModal') {
    document.getElementById('signupForm').reset();
    document.getElementById('signupError').style.display = 'none';
  }
  if (id === 'editModal') {
    document.getElementById('editForm').reset();
    document.getElementById('editError').style.display = 'none';
    editingEventId = null;
  }
}

// Close modal when clicking backdrop
document.querySelectorAll('.modal-backdrop').forEach(el => {
  el.addEventListener('click', e => {
    if (e.target === el) closeModal(el.id);
  });
});

// ---- API calls ----
async function fetchEvents() {
  const res = await fetch(`${API_BASE}/events?type=${activeType}`);
  if (!res.ok) throw new Error('Failed to load events');
  const events = await res.json();

  return events.map(ev => ({
    id: ev.id,
    title: `${ev.f_name} ${ev.l_name}`,
    start: ev.time,
    allDay: true,
    extendedProps: { ...ev },
    classNames: [
      `${ev.missionary_type}-event`,
      ...(isOwnEvent(ev.id) ? ['own-event'] : []),
    ],
  }));
}

async function createEvent(data) {
  const res = await fetch(`${API_BASE}/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Fingerprint-ID': getFingerprint(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Failed to create event');
  }
  const event = await res.json();
  // Remember which events this device created
  markOwnEvent(event.id);
  return event;
}

async function updateEvent(id, data) {
  const res = await fetch(`${API_BASE}/events/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'X-Fingerprint-ID': getFingerprint(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Failed to update event');
  }
  return res.json();
}

async function deleteEvent(id) {
  const res = await fetch(`${API_BASE}/events/${id}`, {
    method: 'DELETE',
    headers: { 'X-Fingerprint-ID': getFingerprint() },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Failed to delete event');
  }
  unmarkOwnEvent(id);
}

// ---- Ownership tracking (localStorage) ----
// The server enforces ownership via X-Fingerprint-ID on DELETE.
// We also track event IDs locally so we can show the delete button on this device's signups.
function ownedEvents() {
  return JSON.parse(localStorage.getItem('meal_roster_owned') || '[]');
}
function markOwnEvent(id) {
  const owned = ownedEvents();
  if (!owned.includes(id)) owned.push(id);
  localStorage.setItem('meal_roster_owned', JSON.stringify(owned));
}
function unmarkOwnEvent(id) {
  const owned = ownedEvents().filter(x => x !== Number(id));
  localStorage.setItem('meal_roster_owned', JSON.stringify(owned));
}
function isOwnEvent(id) {
  return ownedEvents().includes(Number(id));
}

// ---- Signup form submit ----
async function submitSignup(e) {
  e.preventDefault();
  const errEl = document.getElementById('signupError');
  errEl.style.display = 'none';

  const payload = {
    f_name: document.getElementById('f_name').value.trim(),
    l_name: document.getElementById('l_name').value.trim(),
    phone_num: document.getElementById('phone_num').value.trim(),
    // Combine the clicked date with noon UTC so it's always future-safe
    time: pendingDate + 'T12:00:00Z',
    missionary_type: activeType,
  };
  const desc = document.getElementById('description').value.trim();
  if (desc) payload.description = desc;

  try {
    await createEvent(payload);
    closeModal('signupModal');
    showToast('You\'re signed up — thank you!');
    calendar.refetchEvents();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = 'block';
  }
}

// ---- Edit signup ----
function openEditModal(props, id) {
  editingEventId = Number(id);
  // The event time is an ISO datetime; we want YYYY-MM-DD for the date input.
  const isoDate = new Date(props.time).toISOString().slice(0, 10);
  document.getElementById('edit_date').value = isoDate;
  document.getElementById('edit_missionary_type').value = props.missionary_type;
  document.getElementById('edit_description').value = props.description || '';
  document.getElementById('editPersonLabel').textContent = `${props.f_name} ${props.l_name}`;
  document.getElementById('editError').style.display = 'none';
  openModal('editModal');
}

async function submitEdit(e) {
  e.preventDefault();
  const errEl = document.getElementById('editError');
  errEl.style.display = 'none';

  if (editingEventId === null) return;

  const payload = {
    time: document.getElementById('edit_date').value + 'T12:00:00Z',
    missionary_type: document.getElementById('edit_missionary_type').value,
    description: document.getElementById('edit_description').value.trim(),
  };

  try {
    await updateEvent(editingEventId, payload);
    closeModal('editModal');
    showToast('Signup updated.');
    calendar.refetchEvents();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = 'block';
  }
}

// ---- Event detail modal ----
function showDetail(info) {
  const ev = info.event;
  const props = ev.extendedProps;
  const own = isOwnEvent(ev.id);

  document.getElementById('detailDate').textContent = ev.start.toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });

  const body = document.getElementById('detailBody');
  body.innerHTML = '';

  const name = document.createElement('p');
  name.className = 'event-detail-name';
  name.textContent = `${props.f_name} ${props.l_name}`;
  body.appendChild(name);

  const phone = document.createElement('p');
  phone.className = 'event-detail-meta';
  phone.textContent = props.phone_num;
  body.appendChild(phone);

  if (props.description) {
    const desc = document.createElement('p');
    desc.className = 'event-detail-meta';
    desc.textContent = props.description;
    body.appendChild(desc);
  }

  const actions = document.getElementById('detailActions');
  actions.innerHTML = '';
  actions.style.justifyContent = own ? 'space-between' : 'flex-end';

  if (own) {
    const delBtn = document.createElement('button');
    delBtn.className = 'btn btn-danger';
    delBtn.textContent = 'Cancel signup';
    delBtn.onclick = async () => {
      if (!confirm('Are you sure you want to cancel your signup?')) return;
      try {
        await deleteEvent(Number(ev.id));
        closeModal('detailModal');
        showToast('Signup cancelled.');
        calendar.refetchEvents();
      } catch (err) {
        showToast('Error: ' + err.message);
      }
    };
    actions.appendChild(delBtn);

    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-primary';
    editBtn.textContent = 'Edit signup';
    editBtn.onclick = () => {
      closeModal('detailModal');
      openEditModal(props, ev.id);
    };
    actions.appendChild(editBtn);
  }

  const closeBtn = document.createElement('button');
  closeBtn.className = 'btn btn-ghost';
  closeBtn.textContent = 'Close';
  closeBtn.onclick = () => closeModal('detailModal');
  actions.appendChild(closeBtn);

  openModal('detailModal');
}

// ---- Calendar init ----
document.addEventListener('DOMContentLoaded', () => {
  const calEl = document.getElementById('calendar');
  calendar = new FullCalendar.Calendar(calEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,listMonth',
    },
    height: 'auto',
    noEventsText: 'No events scheduled',
    events: async (_info, successCb, failureCb) => {
      try {
        let events = await fetchEvents();
        if (calendar.view.type.startsWith('list')) {
          const now = new Date();
          events = events.filter(e => new Date(e.start) >= now);
        }
        successCb(events);
      } catch (err) {
        failureCb(err);
        showToast('Could not load events — is the server running?');
      }
    },

    // Click an empty day cell → open signup form
    dateClick: (info) => {
      const clickedDate = new Date(info.dateStr);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (clickedDate < today) return; // don't allow past dates

      pendingDate = info.dateStr;
      document.getElementById('signupModalTitle').textContent =
        'Sign up for ' + clickedDate.toLocaleDateString('en-US', {
          weekday: 'long', month: 'long', day: 'numeric',
        });
      openModal('signupModal');
    },

    // Click an existing event → show detail
    eventClick: (info) => {
      info.jsEvent.preventDefault();
      showDetail(info);
    },
  });

  calendar.render();
});
