PERSON = {
    'phone_num': '0400000000',
    'f_name': 'Jane',
    'l_name': 'Smith',
}

FINGERPRINT = '11111111-1111-1111-1111-111111111111'
OTHER_FINGERPRINT = '22222222-2222-2222-2222-222222222222'


def create_group(client, missionary_type='elders', ward='Brisbane'):
    r = client.post(
        '/calendar/group',
        json={'ward': ward, 'missionary_type': missionary_type},
    )
    return r.get_json()['id']


def post_event(client, time='2099-01-01T12:00:00', fingerprint=FINGERPRINT, group_id=None, missionary_type='elders', **overrides):
    if group_id is None:
        group_id = create_group(client, missionary_type=missionary_type)
    payload = {**PERSON, 'time': time, 'group_id': group_id, **overrides}
    return client.post(
        '/calendar/events',
        json=payload,
        headers={'X-Fingerprint-ID': fingerprint},
    )
