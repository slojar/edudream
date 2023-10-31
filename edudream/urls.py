from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("home.urls")),
    path('parent/', include("parent.urls")),
    path('student/', include("student.urls")),
    path('superadmin/', include("superadmin.urls")),
    path('tutor/', include("tutor.urls")),
    path('location/', include("location.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

