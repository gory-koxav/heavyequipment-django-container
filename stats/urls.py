from django.urls import path
from .views import ProcessDataView

urlpatterns = [
    path('process-data/', ProcessDataView.as_view(), name='process-data'),
]