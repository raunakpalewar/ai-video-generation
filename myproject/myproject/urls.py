
from django.contrib import admin
from django.urls import include, path
from main.views import *
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# from settings import static

schema_view = get_schema_view(
   openapi.Info(
      title="ai video generator",
      default_version='v1',
      description="Test description",
    #   terms_of_service="https://www.google.com/policies/terms/",
    #   contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),

   
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
   path('admin/', admin.site.urls),
   path('',schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('url/snapshot/',FetchScreenShot.as_view()),
   path('video/AIVideo/',AIVideoCreation.as_view()),
   path('speechtotext/',SpeechToText.as_view()),
   path('video/MultipleAIVideo/',MultipleAIVideoCreation.as_view()),
   path('video/MultipleAIVideowiththread/',AIvideoCreationWithMultiTreading.as_view()),
   # path('video/VideoCreationWithPostion',VideoCreationWithPostion.as_view()),
   path('mysql/Get_BaseVideo_sql',Get_BaseVideo_sql.as_view()),
   path('VideoCreationWithPostion/',VideoCreationWithPostion.as_view()),
   path('GetAllTagsDetail/',GetAllTagsDetail.as_view()),
   path('CreateTag/',CreateTag.as_view()),
   path('Get_customers/',Get_customers.as_view()),
   path("Videos_for_Customer/",Videos_for_Customer.as_view()),
   path('Get_customers2/',Get_customers2.as_view()),
   path("Videos_for_Customer2/",Videos_for_Customer2.as_view()),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) +static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
