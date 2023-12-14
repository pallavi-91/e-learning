from huey.contrib.djhuey import db_task
from django.utils.timezone import localdate
from apps.utils.certgen import generate_certificate
import os
from django.core.files import File 
from django.conf import settings
from apps.users.models import NotificationSettings

@db_task(name="User class generate certificate")
def class_generate_certificate(user_class):
    certificate_number = hash(user_class.code)
    data = {
        '[certificate-no]': certificate_number,
        '[certificate-url]': os.path.join(settings.SITE_URL, 'course', 'certificate', str(certificate_number)),
        '[full-name]': user_class.user.fullname,
        '[course-title]': user_class.course.title,
        '[instructor-signature]': user_class.course.user.fullname,
        '[instructor-name]': user_class.course.user.fullname,
        '[complete-date]': localdate().strftime('%B %d %Y'),
    }
    certificate_path = generate_certificate(data)
    user_class.certificate.save(
        os.path.basename(certificate_path),
        File(open(certificate_path, 'rb'))
    )
    user_class.certificate_number = certificate_number
    user_class.save()
    os.remove(certificate_path) # Remove file
    
@db_task(name="Create instructor notification settings")
def create_notification_setting(user):
    if not hasattr(user, 'notification_settings'):
        NotificationSettings.objects.create(user=user)