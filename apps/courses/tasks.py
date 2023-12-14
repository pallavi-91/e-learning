import time
from huey.contrib.djhuey import db_periodic_task, db_task
from huey import crontab
from django.conf import settings
from django.conf.global_settings import LANGUAGES
import os, json, boto3
from django.db.models import Q
from apps.status import CourseType, CourseSkillLevel
import numpy as np
from smart_open import open as sopen
import qencode
import re
import json
from qencode import QencodeClientException, QencodeTaskException
from qencode import generate_aws_signed_url

qencode_client = qencode.client(settings.QENCODE_API_KEY)
# Upload course videos
@db_task(retries=2)
def handle_video_uploading(content, bucket_name, object_key, instance):
    s3params = {
        'aws_access_key_id' : instance.access_key,
        'aws_secret_access_key' : instance.secret_key,
        'aws_session_token' : instance.security_token,
        'region_name' : instance.region_name,
    }
    session = boto3.Session(**s3params)
    s3_client = session.client('s3')
    endpointUrl = s3_client.meta.endpoint_url
    s3_client = session.client('s3', endpoint_url=endpointUrl)
    destination = f"s3://{bucket_name}/{object_key}"
    with sopen(destination, 'wb', transport_params={'client': s3_client}) as ff:
        ff.write(content)
    
    s3params.update({
        'bucket_name': bucket_name,
        'object_key': object_key,
        'endpoint_url': endpointUrl
    })

    process_video_transcoding(s3params) # trigger transacoding


@db_task(retries=2)
def process_video_transcoding(s3params):
    from apps.courses.models.courses import Course

    region = s3params.get('region_name')
    bucket_name = s3params.get('bucket_name')
    object_key = s3params.get('object_key')
    access_key = s3params.get('aws_access_key_id')
    secret_key = s3params.get('aws_secret_access_key')
    endpoint_url = s3params.get('endpoint_url').replace('https:', 's3:')
    expiration = 86400  # time in seconds

    source_url = generate_aws_signed_url(region, bucket_name, object_key, access_key, secret_key, expiration)
    
    if qencode_client.error:
        raise QencodeClientException(qencode_client.message)
    
    # Get video code
    resolutions = [
        {"video_codec":"libx264","height":1080,"audio_bitrate":128,"optimize_bitrate": 1},
        {"video_codec":"libx264","height":720,"audio_bitrate":128,"optimize_bitrate": 1},
        {"video_codec":"libx264","height":480,"audio_bitrate":128,"optimize_bitrate": 1},
        {"video_codec":"libx264","height":360,"audio_bitrate":128,"optimize_bitrate": 1}]
    
    code = re.search('(\w+)-(\w+)-(\w+)-(\w+)-(\w+)', object_key)
    if code:
        code = code.group()
        def get_destination(key_size):
            obj = qencode.destination()
            destination_url = f"{code}/dest/{key_size}".join(object_key.split(code))
            destination_url = f"{endpoint_url}/{bucket_name}/{destination_url}"
            obj.url = destination_url
            obj.key = access_key
            obj.secret = secret_key
            obj.permissions = 'private'
            return obj.__dict__
    
        format_dash = dict(
            output="advanced_dash",
            segment_duration=6,
            stream=resolutions,
            create_m3u8_playlist=1,
            destination=get_destination('mpeg-dash')
        )
        query = dict(
            source=source_url,
            format=[format_dash]
        )
        params = dict(query=query)
        task = qencode_client.create_task()
        if task.error:
            raise QencodeTaskException(task.message)

        task.custom_start(params)
        if task.error:
            raise QencodeTaskException(task.message)
        print('Start encode. Task: {0}'.format(task.task_token))
        
        while True:
            course = Course.objects.get(code=code)
            status = task.status()
            # print status
            print(json.dumps(status, indent=2, sort_keys=True))
            if status['error']:
                break
            time.sleep(2)
            course.video_info = {
                "status": status.get('status'),
                "duration": status.get('source_duration'),
                "size": status.get('source_size'),
            }
            if status.get('videos'):
                course.video_info.update({
                    "storage": status.get('videos')[0].get('storage'),
                    "playback": {
                        "url": status.get('videos')[0].get('url')
                    }
                })
            course.save()
            if status['status'] == 'completed':
                break



# Prepare the cache file for filter the courses as metadata
@db_periodic_task(crontab(minute='0', hour='*/5'))
def cache_filter_metadata():
    """
        Every 5th hours this will execute and cache the filter data
    """
    from apps.courses.models import Course, Topic

    cache_file = os.path.join(settings.BASE_DIR, 'core', 'course-filter-meta.json')
    context = dict()
    queryset = Course.objects.all()
    # Get languages data
    
    languages = [dict(zip(('skey', 'name'), i)) for i in LANGUAGES]
    for item in languages:
        total_course = queryset.filter(language=item.get('id')).count()
        item.update({'count': total_course})
    
    context['language'] = languages

    # Get price count data
    prices = []
    for k,v in CourseType.choices:
        if CourseType.FREE == k:
            count = queryset.select_related('pricing').filter(pricing__tier_level=0).count()
        else:
            count = queryset.select_related('pricing').filter(pricing__tier_level__gt=0).count()
        prices.append({
            'skey': k,
            'name': v,
            'count': count
        })
    context['price'] = prices

    # Get course hours length basis count
    
    lengths = [
        {
            "name": "0-1 hours",
            "skey": 0,
        },
        {
            "name": "1-3 hours",
            "skey": 1,
        },
        {
            "name": "3-6 hours",
            "skey": 3,
        },
        {
            "name": "6-10 hours",
            "skey": 6,
        },
        {
            "name": "10+ hours",
            "skey": 10,
        }
    ]
    # 0-1 hours
    
    one_hour = 3600
    three_hours = one_hour * 3
    six_hours = one_hour * 6
    ten_hours = one_hour * 10 
    
    for l in lengths:
        # 0-1 hours
        if l.get('skey') == 0:
            q = Q()
            q = q | Q(id__in=[x.id for x in queryset if x.duration <= one_hour ])
            l['count'] = queryset.filter(q).count()
        # 1-3 hours
        if l.get('skey') == 1:
            q = Q()
            q = q | Q(id__in=[x.id for x in queryset if x.duration > one_hour and x.duration <= three_hours])
            l['count'] = queryset.filter(q).count()
        # 3-6 hours
        if l.get('skey') == 3:
            q = Q()
            q = q | Q(id__in=[x.id for x in queryset if x.duration > three_hours and x.duration <= six_hours ])
            l['count'] = queryset.filter(q).count()
        # 6-10 hours
        if l.get('skey') == 6:
            q = Q()
            q = q | Q(id__in=[x.id for x in queryset if x.duration > six_hours and x.duration <= ten_hours ])
            l['count'] = queryset.filter(q).count()
        # 10+ hours
        if l.get('skey') == 10:
            q = Q()
            q = q | Q(id__in=[x.id for x in queryset if x.duration > ten_hours ])
            l['count'] = queryset.filter(q).count()
    
    context['length'] = lengths

    # Get coirses count by ratings
    ratings = []

    for i in np.arange(0, 6, 0.5):
        # full number rating
        q = Q()
        q = q | Q(id__in=[x.id for x in queryset if x.total_rate >= round(i) and x.total_rate <= i])
        full_rate = {
            "name": f"{i} & up",
            "skey": i,
            "count": queryset.filter(q).count()
        }
        ratings.append(full_rate)

    context['rating'] = ratings

    # Get course count data by level
    levels = []
    for k,v in CourseSkillLevel.choices:
        count = queryset.filter(skill_level=k).count()
        levels.append({
            'skey': k,
            'name': v,
            'count': count
        })
    context['level'] = levels

    # Get course count data by level
    topics_data = []
    for topic in Topic.objects.all():
        count = queryset.filter(topics=topic).count()
        topics_data.append({
            'skey': topic.id,
            'name': topic.name,
            'count': count
        })
    context['topic'] = topics_data
    
    with open(cache_file, 'w') as file:
        file.write(json.dumps(context))