from django.conf import settings
from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=128)
    class_level = models.CharField(max_length=64)
    teacher = models.ForeignKey('teachers.TeacherProfile', on_delete=models.CASCADE, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


from django.core.exceptions import ValidationError


class LearningMaterial(models.Model):
    MATERIAL_TYPES = [
        ('pdf', 'PDF'),
        ('doc', 'Word document'),
        ('video', 'Video'),
        ('note', 'Note'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=16, choices=MATERIAL_TYPES)
    file_path = models.FileField(upload_to='course_materials/', max_length=500, blank=True, null=True)
    note_text = models.TextField(blank=True)
    message_text = models.TextField(blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        allowed_extensions = {
            'pdf': {'.pdf'},
            'doc': {'.doc', '.docx'},
            'video': {'.mp4', '.mov', '.avi', '.webm'},
            'note': set(),
        }

        if self.material_type == 'note':
            if not self.note_text:
                raise ValidationError({'note_text': 'Enter note text for note materials.'})
            if self.file_path:
                raise ValidationError({'file_path': 'Notes should not include a file attachment.'})
            return

        if not self.file_path:
            raise ValidationError({'file_path': 'A file is required for this material type.'})
        if self.note_text:
            raise ValidationError({'note_text': 'Only note materials may include note text.'})

        extension = self.file_path.name.lower().rsplit('.', 1)[-1] if self.file_path.name else ''
        valid_extensions = allowed_extensions.get(self.material_type, set())
        if extension and valid_extensions:
            normalized_extensions = {f'.{extension}'}
            if not normalized_extensions & valid_extensions:
                raise ValidationError({'file_path': 'Only PDF, DOC, DOCX, MP4, MOV, AVI, and WEBM files are allowed.'})

    def get_media_mime_type(self):
        if not self.file_path:
            return None

        filename = self.file_path.name.lower()
        if filename.endswith('.mp4'):
            return 'video/mp4'
        if filename.endswith('.mov'):
            return 'video/quicktime'
        if filename.endswith('.avi'):
            return 'video/x-msvideo'
        if filename.endswith('.webm'):
            return 'video/webm'
        return None

    def __str__(self):
        return f"{self.title} ({self.material_type})"


class Enrollment(models.Model):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"


class VideoWatchProgress(models.Model):
    material = models.ForeignKey(LearningMaterial, on_delete=models.CASCADE, related_name='watch_progress')
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='video_watch_progress')
    watched_complete = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('material', 'student')

    def __str__(self):
        return f"{self.student} - {self.material} - {'complete' if self.watched_complete else 'in progress'}"
