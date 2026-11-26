from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'recommended_material', 'date_generated')
    search_fields = ('student__user__username', 'course__title', 'reason')
