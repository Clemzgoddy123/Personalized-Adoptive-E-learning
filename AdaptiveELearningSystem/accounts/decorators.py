import functools

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy

from students.models import StudentProfile
from teachers.models import TeacherProfile


def student_required(view_func):
    @functools.wraps(view_func)
    @login_required(login_url=reverse_lazy('login'))
    def wrapper(request, *args, **kwargs):
        student_profile = StudentProfile.objects.filter(user=request.user).exists()
        teacher_profile = TeacherProfile.objects.filter(user=request.user).exists()

        if student_profile and not teacher_profile:
            return view_func(request, *args, **kwargs)
        if teacher_profile and not student_profile:
            return redirect('home')
        if student_profile and teacher_profile:
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return wrapper


def teacher_required(view_func):
    @functools.wraps(view_func)
    @login_required(login_url=reverse_lazy('login'))
    def wrapper(request, *args, **kwargs):
        teacher_profile = TeacherProfile.objects.filter(user=request.user).exists()
        student_profile = StudentProfile.objects.filter(user=request.user).exists()

        if teacher_profile and not student_profile:
            return view_func(request, *args, **kwargs)
        if student_profile and not teacher_profile:
            return redirect('home')
        if student_profile and teacher_profile:
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return wrapper
