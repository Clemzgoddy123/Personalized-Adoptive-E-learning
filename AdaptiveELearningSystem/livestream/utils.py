from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import uuid4

from django.utils.text import slugify


def generate_jitsi_room_link(course, scheduled_time):
    course_slug = slugify(course.title or 'live-class')
    room_name = f"adaptive-{course_slug}-{course.pk}-{scheduled_time.strftime('%Y%m%d%H%M')}-{uuid4().hex[:6]}"
    return f"https://meet.jit.si/{room_name}"


def build_jitsi_embed_url(meeting_link, request):
    if not meeting_link:
        return meeting_link

    parsed = urlparse(meeting_link)
    if parsed.netloc.lower() not in {'meet.jit.si', 'meet.jit.si.'}:
        return meeting_link

    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params['embed'] = 'true'
    query_params['mobile'] = 'true'
    query_params['parent'] = request.get_host().split(':')[0]

    return urlunparse(parsed._replace(query=urlencode(query_params), fragment=''))
