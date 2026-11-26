from django import forms

from courses.models import Course
from teachers.models import TeacherProfile

from .models import LiveClass
from .utils import generate_jitsi_room_link


class LiveClassForm(forms.ModelForm):
    class Meta:
        model = LiveClass
        fields = ['course', 'scheduled_time', 'meeting_link']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['meeting_link'].required = False
        self.fields['meeting_link'].help_text = 'Leave blank to auto-generate a new Jitsi meeting room.'

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            teacher_profile = TeacherProfile.objects.filter(user=user).first()
            if teacher_profile:
                self.fields['course'].queryset = Course.objects.filter(teacher=teacher_profile)
            else:
                self.fields['course'].queryset = Course.objects.none()

    def save(self, commit=True, teacher=None):
        instance = super().save(commit=False)
        if teacher is not None:
            instance.teacher = teacher
        if not instance.meeting_link:
            instance.meeting_link = generate_jitsi_room_link(instance.course, instance.scheduled_time)
        if commit:
            instance.save()
        return instance
