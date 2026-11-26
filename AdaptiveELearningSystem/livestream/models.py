from django.db import models


class LiveClass(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='live_classes')
    teacher = models.ForeignKey('teachers.TeacherProfile', on_delete=models.CASCADE, related_name='live_classes')
    scheduled_time = models.DateTimeField()
    meeting_link = models.URLField(max_length=500)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.title} live class at {self.scheduled_time}"
