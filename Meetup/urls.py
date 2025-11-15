from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# URL patterns
urlpatterns = [
    path("", views.home, name="home"),
    path("userProfile/", views.userProfile, name="userProfile"),
    path("modifyProfile/", views.modifyProfile, name="modifyProfile"),
    path("deleteUser/", views.deleteUser, name="deleteUser"),
    path("activities/", views.activities, name="activities"),
    path('add/', views.add_activity, name='add'),
    path('modifyActivity/<int:activity_id>/', views.modify_activity, name='modifyActivity'),
    path('activity/review/<int:id>/', views.activity_review, name='activity_review'),
    path('ActDetail/<int:activity_id>/', views.activityDetail, name='ActDetail'),
    path('ActDetail/<int:activity_id>/comment/', views.add_comment, name='add_comment'),
    path("activitiesmanage/", views.activitiesmanage, name="activitiesmanage"),
    path("report/", views.report_issue, name="report_issue"),
    path("login/", auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path("logout/", auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path("register/", views.RegisterView.as_view(), name='register'),
    path("chat/", views.chat_home, name="chat_home"),
    path("chat/create/", views.create_conversation, name="create_conversation"),
    path("chat/<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),
    path("chat/<int:conversation_id>/messages/", views.get_messages, name="get_messages"),
    path('activity/<int:activity_id>/request-join/', views.request_to_join, name='request_to_join'),
    path('requests/', views.manage_requests, name='manage_requests'),
    path('request/<int:request_id>/handle/', views.handle_request, name='handle_request'),
]