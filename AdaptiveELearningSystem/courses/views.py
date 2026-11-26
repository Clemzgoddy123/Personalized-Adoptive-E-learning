from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Course


@login_required
def course_list(request):
    courses = Course.objects.select_related('teacher').all()
    return render(request, 'courses/course_list.html', {'courses': courses})


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    materials = course.materials.all()
    return render(request, 'courses/course_detail.html', {'course': course, 'materials': materials})
