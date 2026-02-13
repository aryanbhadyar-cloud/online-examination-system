from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Teacher
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/create/', views.teacher_create_exam, name='teacher_create_exam'),
    path('teacher/exam/<int:exam_id>/', views.teacher_exam_detail, name='teacher_exam_detail'),
    path('teacher/exam/<int:exam_id>/results/', views.teacher_exam_results, name='teacher_exam_results'),
    path('teacher/students/', views.teacher_student, name='teacher_student'),


    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/exam/<int:exam_id>/', views.student_take_exam, name='student_take_exam'),
    path('student/history/', views.student_history, name='student_history'),
]
