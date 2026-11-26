from dataclasses import dataclass
from decimal import Decimal

from django.db import models
from django.db.models import Avg, Count
from django.utils import timezone


@dataclass
class RecommendationItem:
    title: str
    course_title: str
    reason: str
    recipient_name: str | None = None
    recommended_material_title: str | None = None
    date_generated: str | None = None
    source: str = 'computed'


class Recommendation(models.Model):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='recommendations')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='recommendations')
    recommended_material = models.ForeignKey('courses.LearningMaterial', on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendations')
    reason = models.TextField()
    date_generated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.student} in {self.course}"

    @classmethod
    def get_recommendations_for_user(cls, user):
        from students.models import StudentProfile
        from teachers.models import TeacherProfile

        student_profile = StudentProfile.objects.filter(user=user).first()
        if student_profile:
            return cls._recommend_for_student(student_profile)

        teacher_profile = TeacherProfile.objects.filter(user=user).first()
        if teacher_profile:
            return cls._recommend_for_teacher(teacher_profile)

        return []

    @classmethod
    def _recommend_for_student(cls, student_profile):
        from assignments.models import Assignment, AssignmentSubmission
        from courses.models import LearningMaterial
        from livestream.models import LiveClass
        from quizzes.models import QuizResult

        recommendations = []
        course_ids = [enrollment.course.id for enrollment in student_profile.enrollments.select_related('course')]
        user_name = student_profile.user.get_full_name() or student_profile.user.username
        now = timezone.now()

        pending_assignments = Assignment.objects.filter(course_id__in=course_ids, deadline__gte=now).select_related('course').order_by('deadline')[:3]
        for assignment in pending_assignments:
            recommendations.append(RecommendationItem(
                title=f"Review work for {assignment.title}",
                course_title=assignment.course.title,
                reason=f"You have an upcoming assignment due {assignment.deadline:%Y-%m-%d %H:%M}. Review course materials for best results.",
                recipient_name=user_name,
                date_generated=now.isoformat(),
            ))

        recent_results = QuizResult.objects.filter(student=student_profile).select_related('quiz__course').order_by('score')[:3]
        for result in recent_results:
            threshold = Decimal(result.quiz.total_marks) * Decimal('0.7')
            if result.score < threshold:
                recommendations.append(RecommendationItem(
                    title=f"Improve your quiz performance in {result.quiz.course.title}",
                    course_title=result.quiz.course.title,
                    reason=f"Your score of {result.score} on {result.quiz.title} suggests reviewing the course materials.",
                    recipient_name=user_name,
                    date_generated=result.date_taken.isoformat(),
                ))

        recent_materials = LearningMaterial.objects.filter(course_id__in=course_ids).order_by('-upload_date')[:3]
        for material in recent_materials:
            recommendations.append(RecommendationItem(
                title=f"Study: {material.title}",
                course_title=material.course.title,
                recommended_material_title=material.title,
                reason=f"This material is recent and relevant to your enrolled course.",
                recipient_name=user_name,
                date_generated=material.upload_date.isoformat(),
            ))

        upcoming_live_classes = LiveClass.objects.filter(course_id__in=course_ids, scheduled_time__gte=now).select_related('course').order_by('scheduled_time')[:2]
        for live_class in upcoming_live_classes:
            recommendations.append(RecommendationItem(
                title=f"Attend live class for {live_class.course.title}",
                course_title=live_class.course.title,
                reason=f"A live class is scheduled on {live_class.scheduled_time:%Y-%m-%d %H:%M}. Join to strengthen your understanding.",
                recipient_name=user_name,
                date_generated=live_class.scheduled_time.isoformat(),
            ))

        if not recommendations:
            recommendations.append(RecommendationItem(
                title="Stay engaged with your enrolled courses",
                course_title=student_profile.enrollments.first().course.title if student_profile.enrollments.exists() else 'General',
                reason="Keep up with assignments, quizzes and course materials to maintain strong progress.",
                recipient_name=user_name,
                date_generated=now.isoformat(),
            ))

        return recommendations

    @classmethod
    def _recommend_for_teacher(cls, teacher_profile):
        from assignments.models import AssignmentSubmission
        from attendance.models import AttendanceRecord
        from quizzes.models import QuizResult

        recommendations = []
        courses = teacher_profile.courses.all()
        user_name = teacher_profile.user.get_full_name() or teacher_profile.user.username
        now = timezone.now()

        ungraded = AssignmentSubmission.objects.filter(assignment__course__in=courses, score__isnull=True).select_related('assignment__course')
        if ungraded.exists():
            course_counts = {}
            for submission in ungraded:
                course_title = submission.assignment.course.title
                course_counts[course_title] = course_counts.get(course_title, 0) + 1
            for course_title, count in course_counts.items():
                recommendations.append(RecommendationItem(
                    title=f"Grade submissions for {course_title}",
                    course_title=course_title,
                    reason=f"You have {count} ungraded submissions waiting for review.",
                    recipient_name=user_name,
                    date_generated=now.isoformat(),
                ))

        low_attendance = AttendanceRecord.objects.filter(course__in=courses, status='absent').values('course__title').annotate(absences=Count('id')).order_by('-absences')[:3]
        for data in low_attendance:
            recommendations.append(RecommendationItem(
                title=f"Improve attendance in {data['course__title']}",
                course_title=data['course__title'],
                reason=f"There are {data['absences']} absence records. Consider a review or student check-in.",
                recipient_name=user_name,
                date_generated=now.isoformat(),
            ))

        quiz_stats = QuizResult.objects.filter(quiz__course__in=courses).select_related('quiz__course')
        course_scores = {}
        for result in quiz_stats:
            course = result.quiz.course
            entry = course_scores.setdefault(course.title, {'total': Decimal('0'), 'count': 0})
            entry['total'] += result.score
            entry['count'] += 1
        for course_title, data in course_scores.items():
            avg_score = data['total'] / data['count']
            if avg_score < Decimal('70'):
                recommendations.append(RecommendationItem(
                    title=f"Support {course_title} students with review materials",
                    course_title=course_title,
                    reason=f"Average quiz score is {avg_score:.1f}. Provide additional practice or review sessions.",
                    recipient_name=user_name,
                    date_generated=now.isoformat(),
                ))

        if not recommendations:
            recommendations.append(RecommendationItem(
                title="Continue supporting your courses",
                course_title=courses.first().title if courses.exists() else 'General',
                reason="Keep engaging with students through assignments, quizzes and announcements.",
                recipient_name=user_name,
                date_generated=now.isoformat(),
            ))

        return recommendations
