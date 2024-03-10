from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls')),
    path('store/', include('store.urls')),
    path('rosetta/', include('rosetta.urls'))
]

if settings.DEBUG is True:
   schema_view = get_schema_view(
         openapi.Info(
            title="Mix Shop API",
            default_version='v1',
            description="These APIs are for a shop project called Mix Shop",
            contact=openapi.Contact(email="mohammadreza.gharghabi6@gmail.com"),
            license=openapi.License(name="MIT License"),
         ),
         permission_classes=(permissions.AllowAny,),
   )

   urlpatterns =  urlpatterns + [
      path('__debug__/', include('debug_toolbar.urls')),  

      path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
      path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
