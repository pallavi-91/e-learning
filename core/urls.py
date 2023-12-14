from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, re_path, include
from rest_framework.schemas import get_schema_view
from rest_framework.permissions import AllowAny
from django.views.static import serve
from django.views.generic.base import TemplateView
from rest_framework.documentation import include_docs_urls
from django.contrib.admin.views.decorators import staff_member_required
from decorator_include import decorator_include

ADMIN_VERSION='v1'

def response_not_found_handler(request):
    return HttpResponseRedirect('/docs')

def current_datetime(request):
    text = request.GET.get("text","")
    html = f'<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150" viewBox="0 0 40 40"><g data-name="Group 3367"><path data-name="Rectangle 23427" d="M0 0h40v40H0z"/><text transform="translate(10 25)" fill="#fff" font-size="16" font-family="Maax"><tspan x="0" y="0">{text}</tspan></text></g></svg>'
    return HttpResponse(html,content_type='image/svg')

urlpatterns = [
    path('djadmin/', admin.site.urls),
    path('api/default-user.svg', current_datetime ),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^assets/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path('', response_not_found_handler),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

marketfront_url_patterns = [
    path(f'api/{ADMIN_VERSION}/', include('apps.apis.urls')),
]
urlpatterns += marketfront_url_patterns

urlpatterns += [
    path('schema', get_schema_view(
            title="Thkee APIs",
            description="API for marketplace",
            version="1.0.0",
            patterns=marketfront_url_patterns,
            permission_classes=[AllowAny]
        ), name='openapi-schema'),
    re_path('docs/', decorator_include(staff_member_required, include_docs_urls(title="API Documentation", public=False))),
]