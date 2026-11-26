from django.db import models


class Quiz(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    total_marks = models.PositiveIntegerField(default=100)
    duration_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course})"

    @property
    def question_count(self):
        return self.quiz_questions.count()


class Question(models.Model):
    ANSWER_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_choice = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    marks = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course}: {self.text[:60]}"


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='quiz_assignments')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('quiz', 'question')
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order + 1}"


class QuizResult(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='quiz_results')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    date_taken = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('quiz', 'student')

    def __str__(self):
        return f"{self.student} - {self.quiz}: {self.score}"
