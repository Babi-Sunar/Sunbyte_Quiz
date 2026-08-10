from django.urls import path
from . import views

app_name = 'quizapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('delete-account/', views.delete_account, name='delete_account'),
    path(
    'my-quizzes/',
    views.my_quizzes,
    name='my_quizzes'
    ),
    path(
    "session/<str:code>/delete/",
    views.delete_session,
    name="delete_session",
    ),
    path(
    "session/<str:code>/results/",
    views.session_results,
    name="session_results",
    ),
    path(
    "host-session/<str:code>/host/",
    views.host_room,
    name="host_room",
    ),
    path(
    "session/<str:code>/start/",
    views.start_quiz,
    name="start_quiz",
    ),
    path(
    "session/<str:code>/pause/",
    views.pause_quiz,
    name="pause_quiz",
    ),

    path(
    "session/<str:code>/resume/",
    views.resume_quiz,
    name="resume_quiz",
    ),
    path(
    "session/<str:code>/next-question/",
    views.next_question,
    name="next_question",
    ),
    path(
    "session/<str:code>/participant-count/",
    views.participant_count,
    name="participant_count",
    ),
    path(
    "session/<str:code>/final-room/",
    views.final_room,
    name="final_room",
    ),
    path(
    "session/<str:code>/check-question-timer/",
    views.check_question_timer,
    name="check_question_timer",
    ),
    path(
    "session/<str:code>/status/",
    views.session_status,
    name="session_status"
    ),
    path(
    "session/<str:code>/quiz-status/",
    views.quiz_status,
    name="quiz_status",
    ),
    path(
    "session/<str:code>/participant-list/",
    views.participant_list,
    name="participant_list",
    ),
    path(
    "session/<str:code>/save-answer/",
    views.save_answer,
    name="save_answer",
    ),

    path(
    "session/<str:code>/submit/",
    views.submit_quiz,
    name="submit_quiz",
    ),
    path(
    "session/<str:code>/results/pdf/",
    views.download_results_pdf,
    name="download_results_pdf",
    ),
    path(
    "delete-account/",
    views.delete_account,
    name="delete_account"
    ),
    path(
    "add-category/",
    views.add_category,
    name="add_category"
    ),
    path(
    'verify-email/<uidb64>/<token>/',
    views.verify_email_view,
    name='verify_email'
    ),
    path(
    'forgot-password/',
    views.forgot_password_view,
    name='forgot_password'
    ),

    path(
    'reset-password/<uidb64>/<token>/',
    views.reset_password_view,
    name='reset_password'
    ),

    # Joining — no account required
    path('session/join/', views.join_session, name='join_session'),

    # Hosting / building a quiz
    path('session/create/', views.create_session, name='create_session'),
    path('session/<str:code>/manage/', views.manage_session, name='manage_session'),
    path('session/<str:code>/questions/add/', views.add_question, name='add_question'),
    path('session/<str:code>/questions/<int:question_id>/edit/', views.edit_question, name='edit_question',),
    path('session/<str:code>/questions/<int:question_id>/delete/',views.delete_question,name='delete_question',),
    path('session/<str:code>/publish/', views.publish_session, name='publish_session'),
    path('session/<str:code>/end/', views.end_session, name='end_session'),

    # Lobby / attempt / results
    path('session/<str:code>/', views.session_room, name='session_room'),
    path('session/<str:code>/play/', views.take_quiz, name='take_quiz'),
    path('session/<str:code>/result/', views.result_detail, name='result_detail'),
]
