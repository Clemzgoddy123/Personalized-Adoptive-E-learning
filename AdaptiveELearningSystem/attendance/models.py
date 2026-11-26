from django.db import models
from django.utils import timezone


class AttendanceManager(models.Manager):
    def mark_present(self, course, student, date=None):
        """Create or update an attendance record marking a student as present."""
        if date is None:
            date = timezone.localdate()
        obj, created = self.get_or_create(course=course, student=student, date=date,
                                          defaults={'status': 'present'})
        if not created and obj.status != 'present':
            obj.status = 'present'
            obj.save(update_fields=['status'])
        return obj

    def mark_present_for_liveclass(self, live_class, student_profiles):
        """Mark a list of StudentProfile instances as present for a live class's course on the scheduled date."""
        date = live_class.scheduled_time.date()
        created = []
        for student in student_profiles:
            obj, was_created = self.get_or_create(course=live_class.course, student=student, date=date,
                                                  defaults={'status': 'present'})
            if not was_created and obj.status != 'present':
                obj.status = 'present'
                obj.save(update_fields=['status'])
            created.append(obj)
        return created

    def mark_absent_for_liveclass(self, live_class, exclude_students=None):
        """Mark enrolled students absent for a live class date, skipping any in exclude_students or who already have a record."""
        if exclude_students is None:
            exclude_students = []
        date = live_class.scheduled_time.date()
        created = []
        enrollments = live_class.course.enrollments.select_related('student').all()
        exclude_ids = {s.id for s in exclude_students}
        for e in enrollments:
            student = e.student
            if student.id in exclude_ids:
                continue
            # if a record already exists for this date, skip
            if self.filter(course=live_class.course, student=student, date=date).exists():
                continue
            obj = self.create(course=live_class.course, student=student, date=date, status='absent')
            created.append(obj)
        return created



class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student', 'date')

    def __str__(self):
        return f"{self.student} - {self.course} on {self.date}: {self.status}"
    # custom manager
    objects = AttendanceManager()
