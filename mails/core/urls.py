from django.urls import path
from . import views

urlpatterns = [
    path("inbox/", views.open_inbox),
    path("send/", views.send_mail),

    path("mail/<int:mail_id>/", views.open_mail),
    path("mail/<int:mail_id>/delete/", views.delete_mail),

    path("clear/", views.clear_inbox),
    path("refresh/", views.refresh_inbox),

    path("register/", views.register_user),
    path("login/", views.login_user),
    path("logout/", views.logout_user),
]