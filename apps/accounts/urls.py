from django.urls import path
from .views import SignInView, DashboardView

app_name = 'accounts'

urlpatterns = [
    path('login/', SignInView.as_view(), name='signin'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
