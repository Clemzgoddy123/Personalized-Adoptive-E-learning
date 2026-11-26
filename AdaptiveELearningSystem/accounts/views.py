from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import UserRegistrationForm, UserProfileForm
from students.forms import StudentProfileForm
from students.models import StudentProfile
from teachers.forms import TeacherProfileForm
from teachers.models import TeacherProfile


def _append_registration_to_sql_backup(username, email, role):
    backup_path = Path(__file__).resolve().parents[2] / 'e-learning_db.session.sql'
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
    safe_username = username.replace("'", "''")
    safe_email = email.replace("'", "''")
    safe_role = role.replace("'", "''")
    sql_entry = (
        "\n-- Registration backup\n"
        "CREATE TABLE IF NOT EXISTS registered_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, email TEXT NOT NULL, role TEXT NOT NULL, registered_at TEXT NOT NULL);\n"
        f"INSERT INTO registered_users (username, email, role, registered_at) VALUES ('{safe_username}', '{safe_email}', '{safe_role}', '{timestamp}');\n"
    )
    with backup_path.open('a', encoding='utf-8') as handle:
        handle.write(sql_entry)


def register(request):
    next_page = request.POST.get('next', request.GET.get('next', ''))

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            if role == 'student':
                StudentProfile.objects.create(user=user)
            else:
                TeacherProfile.objects.create(user=user)
            _append_registration_to_sql_backup(user.username, user.email, role)
            login(request, user)
            messages.success(request, 'Registration successful. Welcome!')
            if next_page and url_has_allowed_host_and_scheme(next_page, allowed_hosts={request.get_host(), *settings.ALLOWED_HOSTS}):
                return redirect(next_page)
            return redirect('home')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'next_page': next_page})


@login_required
def account_profile(request):
    student_profile = StudentProfile.objects.filter(user=request.user).select_related('user').first()
    teacher_profile = TeacherProfile.objects.filter(user=request.user).select_related('user').first()
    profile = student_profile or teacher_profile

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        if student_profile:
            profile_form = StudentProfileForm(request.POST, request.FILES, instance=student_profile)
        elif teacher_profile:
            profile_form = TeacherProfileForm(request.POST, request.FILES, instance=teacher_profile)
        else:
            profile_form = None

        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('account_profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        if student_profile:
            profile_form = StudentProfileForm(instance=student_profile)
        elif teacher_profile:
            profile_form = TeacherProfileForm(instance=teacher_profile)
        else:
            profile_form = None

    return render(request, 'accounts/account_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })
