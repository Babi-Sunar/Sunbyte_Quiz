from django.urls import path

from . import views

app_name = 'quizapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Joining — no account required
    path('session/join/', views.join_session, name='join_session'),

    # Hosting / building a quiz
    path('session/create/', views.create_session, name='create_session'),
    path('session/<str:code>/manage/', views.manage_session, name='manage_session'),
    path('session/<str:code>/questions/add/', views.add_question, name='add_question'),
    path('session/<str:code>/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('session/<str:code>/publish/', views.publish_session, name='publish_session'),
    path('session/<str:code>/end/', views.end_session, name='end_session'),

    # Lobby / attempt / results
    path('session/<str:code>/', views.session_room, name='session_room'),
    path('session/<str:code>/play/', views.take_quiz, name='take_quiz'),
    path('session/<str:code>/result/', views.result_detail, name='result_detail'),
]
