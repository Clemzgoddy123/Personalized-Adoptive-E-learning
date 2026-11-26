from django.contrib import admin
from .models import Question, Quiz, QuizQuestion, QuizResult


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question', 'order')
    search_fields = ('quiz__title', 'question__text')
    list_filter = ('quiz',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('course', 'text', 'correct_choice', 'marks', 'created_at')
    search_fields = ('text', 'course__title')
    list_filter = ('course',)


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0
    readonly_fields = ('question',)
    fields = ('question', 'order')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'total_marks', 'duration_minutes', 'created_at')
    search_fields = ('title', 'course__title')
    list_filter = ('course__subject',)
    inlines = [QuizQuestionInline]


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'student', 'score', 'date_taken')
    search_fields = ('quiz__title', 'student__user__username')
