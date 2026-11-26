from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Recommendation


@login_required
def recommendation_list(request):
    recommendations = Recommendation.get_recommendations_for_user(request.user)
    return render(request, 'recommendations/recommendation_list.html', {'recommendations': recommendations})
