PERSON = {
    'phone_num': '0400000000',
    'f_name': 'Jane',
    'l_name': 'Smith',
}

FINGERPRINT = '11111111-1111-1111-1111-111111111111'
OTHER_FINGERPRINT = '22222222-2222-2222-2222-222222222222'


def post_event(client, time='2099-01-01T12:00:00', fingerprint=FINGERPRINT, missionary_type='elders', **overrides):
    payload = {**PERSON, 'time': time, 'missionary_type': missionary_type, **overrides}
    return client.post(
        '/calendar/events',
        json=payload,
        headers={'X-Fingerprint-ID': fingerprint},
    )
