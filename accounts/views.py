from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Profile, Course, Subject, Exam, Question, StudentExam, Result


# ===== Login (FIXED FOR FIRST-TIME LOGIN) =====
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            return render(request, 'accounts/login.html', {'error': 'Invalid username'})

        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, 'accounts/login.html', {'error': 'Invalid password'})

        auth_login(request, user)
        
        # Create profile if it doesn't exist (FIX FOR FIRST-TIME LOGIN)
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user, role='student', approved=True)
        
        if hasattr(user, 'profile') and user.profile.role == 'teacher':
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')

    return render(request, 'accounts/login.html')


# ===== Logout =====
def logout_view(request):
    auth_logout(request)
    return redirect('login')


# ===== Teacher dashboard (ENHANCED WITH ANALYSIS) =====
@login_required
def teacher_dashboard(request):
    # Get all exams created by this teacher
    exams = Exam.objects.filter(created_by=request.user).order_by('-id')
    
    # Calculate statistics
    total_students = Profile.objects.filter(role='student', approved=True).count()
    
    completed_exams = StudentExam.objects.filter(
        exam__created_by=request.user, 
        is_submitted=True
    ).count()
    
    all_scores = StudentExam.objects.filter(
        exam__created_by=request.user, 
        is_submitted=True, 
        score__isnull=False
    )
    
    if all_scores.exists():
        scores = [s.score for s in all_scores if s.score is not None]
        average_score = round(sum(scores) / len(scores), 1) if scores else 0
    else:
        average_score = 0
    
    # ENHANCED ANALYSIS DATA (NEW - FOR ANALYSIS BACKEND)
    total_exams = exams.count()
    active_exams = exams.filter(is_active=True) 
    
    # Get per-exam statistics for analysis
    exam_stats = []
    for exam in exams:
        exam_submissions = StudentExam.objects.filter(exam=exam, is_submitted=True)
        exam_scores = [s.score for s in exam_submissions if s.score is not None]
        
        exam_stats.append({
            'exam': exam,
            'submissions': exam_submissions.count(),
            'average': round(sum(exam_scores) / len(exam_scores), 1) if exam_scores else 0,
            'highest': max(exam_scores) if exam_scores else 0,
            'lowest': min(exam_scores) if exam_scores else 0,
            'pass_rate': round(len([s for s in exam_scores if s >= 60]) / len(exam_scores) * 100, 1) if exam_scores else 0
        })
    
    # Top performing students
    top_students = StudentExam.objects.filter(
        exam__created_by=request.user,
        is_submitted=True,
        score__isnull=False
    ).select_related('student', 'exam').order_by('-score')[:5]
    
    # Recent activity
    recent_submissions = StudentExam.objects.filter(
        exam__created_by=request.user,
        is_submitted=True
    ).select_related('student', 'exam').order_by('-id')
    
    context = {
        'exams': exams,
        'total_students': total_students,
        'completed_exams': completed_exams,
        'average_score': average_score,
        'total_exams': total_exams,
        'active_exams': active_exams,
        'exam_stats': exam_stats,
        'top_students': top_students,
        'recent_submissions': recent_submissions,
    }
    
    return render(request, 'accounts/teacher_dashboard.html', context)


# ===== Create Exam (FIXED - TIME FIELDS NOW OPTIONAL) =====
@login_required
def teacher_create_exam(request):
    courses = Course.objects.all()
    subjects = Subject.objects.all()
    
    if request.method == 'POST':
        name = request.POST['name']
        subject_id = request.POST['subject']
        # TIME FIELDS ARE NOW OPTIONAL - removed requirement
        
        allow_calculator = 'allow_calculator' in request.POST

        subject = get_object_or_404(Subject, id=subject_id)
        
        # Create exam without requiring time fields
        exam = Exam.objects.create(
            subject=subject,
            course=subject.course,
            name=name,
            created_by=request.user,
            allow_calculator=allow_calculator
        )
        return redirect('teacher_exam_detail', exam_id=exam.id)

    return render(request, 'accounts/teacher_create_exam.html', {
        'courses': courses, 
        'subjects': subjects
    })


# ===== Exam Detail & Add Questions =====
@login_required
def teacher_exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    questions = Question.objects.filter(exam=exam)

    if request.method == 'POST':
        qtext = request.POST['question_text']
        option1 = request.POST['option1']
        option2 = request.POST['option2']
        option3 = request.POST.get('option3', '')
        option4 = request.POST.get('option4', '')
        correct_option = request.POST['correct_option']

        Question.objects.create(
            exam=exam,
            question_text=qtext,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )
        return redirect('teacher_exam_detail', exam_id=exam.id)

    return render(request, 'accounts/teacher_exam_detail.html', {'exam': exam, 'questions': questions})


# ===== Student dashboard (FIXED FOR "NO EXAM YET") =====
@login_required
def student_dashboard(request):
    # Ensure profile exists
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user, role='student', approved=True)
    
    profile = request.user.profile
    
    # Get exams for student's course (FIX FOR "NO EXAM YET")
    if profile.course:
        exams = Exam.objects.filter(
            subject__course=profile.course,
            is_active=True
        ).select_related('subject', 'subject__course').order_by('-id')
    else:
        exams = Exam.objects.none()
    
    # Calculate statistics
    completed_exams = StudentExam.objects.filter(student=request.user, is_submitted=True)
    completed_count = completed_exams.count()
    
    if completed_count > 0:
        scores = [exam.score for exam in completed_exams if exam.score is not None]
        average_score = round(sum(scores) / len(scores), 1) if scores else 0
    else:
        average_score = 0
    
    pending_count = max(0, exams.count() - completed_count)
    
    context = {
        'exams': exams,
        'completed_count': completed_count,
        'average_score': average_score,
        'pending_count': pending_count,
    }
    
    return render(request, 'accounts/student_dashboard.html', context)


# ===== Take Exam (COMPLETELY FIXED - NO TIME RESTRICTION) =====
@login_required
def student_take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Ensure profile exists
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user, role='student', approved=True)
    
    profile = request.user.profile

    # Check if exam belongs to student's course (FIX FOR ACCESS CONTROL)
    if profile.course and exam.subject.course != profile.course:
        return render(request, 'accounts/student_exams.html', {
            'error': 'You cannot take this exam - it is not for your course.',
            'exams': Exam.objects.filter(subject__course=profile.course, is_active=True)
        })

    # Get questions (FIX FOR "NO QUESTIONS")
    questions = Question.objects.filter(exam=exam)
    
    if not questions.exists():
        return render(request, 'accounts/student_exams.html', {
            'error': 'This exam has no questions yet. Please check back later.',
            'exams': Exam.objects.filter(subject__course=profile.course, is_active=True)
        })

    # Get or create StudentExam instance
    student_exam, created = StudentExam.objects.get_or_create(
        student=request.user, 
        exam=exam,
    )
    
    # Check if already submitted
    if student_exam.is_submitted:
        return render(request, 'accounts/student_exams.html', {
            'error': 'You have already completed this exam.',
            'exams': Exam.objects.filter(subject__course=profile.course, is_active=True)
        })

    # TIME RESTRICTION REMOVED - Students can take exam anytime

    # Handle form submission
    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        
        for question in questions:
            answer = request.POST.get(str(question.id))
            if answer == question.correct_option:
                score += 1
        
        # Calculate percentage
        percentage_score = (score / total_questions * 100) if total_questions > 0 else 0
        
        student_exam.score = percentage_score
        student_exam.is_submitted = True
        
        student_exam.save()
        
        # Also save to Result model for consistency
        Result.objects.create(
            student=profile,
            exam=exam,
            score=percentage_score
        )
        
        return redirect('student_history')

    # Render exam page
    return render(request, 'accounts/student_exams.html', {
        'exam': exam, 
        'questions': questions
    })


# ===== Student Exam History (ENHANCED) =====
@login_required
def student_history(request):
    records = StudentExam.objects.filter(student=request.user, is_submitted=True).order_by('-id')
    
    # Calculate statistics
    completed_records = records.filter(is_submitted=True)
    
    if completed_records.exists():
        scores = [r.score for r in completed_records if r.score is not None]
        
        if scores:
            average_score = round(sum(scores) / len(scores), 1)
            highest_score = max(scores)
            passing_count = len([s for s in scores if s >= 60])
        else:
            average_score = 0
            highest_score = 0
            passing_count = 0
    else:
        average_score = 0
        highest_score = 0
        passing_count = 0
    
    context = {
        'records': records,
        'average_score': average_score,
        'highest_score': highest_score,
        'passing_count': passing_count,
    }
    
    return render(request, 'accounts/student_history.html', context)


# ===== Teacher Exam Results (FIXED TYPO - created_by instead of deleted_by) =====
@login_required
def teacher_exam_results(request, exam_id):
    # FIX: Changed 'deleted_by' to 'created_by' - this was causing the error
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    # Get results from both StudentExam and Result models for comprehensive view
    student_exams = StudentExam.objects.filter(exam=exam, is_submitted=True).select_related('student', 'student__profile')
    results = Result.objects.filter(exam=exam).select_related('student', 'student__user')
    
    # Calculate exam statistics
    if student_exams.exists():
        scores = [se.score for se in student_exams if se.score is not None]
        if scores:
            exam_stats = {
                'total_attempts': student_exams.count(),
                'average_score': round(sum(scores) / len(scores), 1),
                'highest_score': max(scores),
                'lowest_score': min(scores),
                'pass_count': len([s for s in scores if s >= 60]),
                'fail_count': len([s for s in scores if s < 60]),
                'pass_percentage': round(len([s for s in scores if s >= 60]) / len(scores) * 100, 1) if scores else 0
            }
        else:
            exam_stats = {
                'total_attempts': 0,
                'average_score': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'pass_count': 0,
                'fail_count': 0,
                'pass_percentage': 0
            }
    else:
        exam_stats = {
            'total_attempts': 0,
            'average_score': 0,
            'highest_score': 0,
            'lowest_score': 0,
            'pass_count': 0,
            'fail_count': 0,
            'pass_percentage': 0
        }
    
    return render(request, 'accounts/teacher_exam_results.html', {
        'exam': exam, 
        'results': results,
        'student_exams': student_exams,
        'exam_stats': exam_stats
    })






@login_required
def teacher_student(request):
    # Only teachers allowed
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teacher':
        return redirect('login')

    teacher = request.user

    # Get all courses where this teacher has created exams
    teacher_courses = Course.objects.filter(
        subject__exam__created_by=teacher
    ).distinct()

    # Get all students enrolled in those courses
    students = Profile.objects.filter(
        role='student',
        approved=True,
        course__in=teacher_courses
    ).select_related('user', 'course')

    context = {
        'students': students,
    }

    return render(request, 'accounts/teacher_student.html', context)
