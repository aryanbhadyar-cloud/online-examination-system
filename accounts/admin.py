from django.contrib import admin
from .models import Profile, Course, Subject, Exam, Question, StudentExam

# Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'approved', 'roll_number', 'course')

# Course
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)

# Subject
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')

# Exam
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject',  'created_by', 'allow_calculator', 'is_active')
    list_filter = ('subject', 'created_by', 'is_active')

# Question
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'exam', 'correct_option')

# StudentExam
@admin.register(StudentExam)
class StudentExamAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'is_submitted', )
