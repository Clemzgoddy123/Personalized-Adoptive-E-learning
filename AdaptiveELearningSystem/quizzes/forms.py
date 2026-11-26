from django import forms
from django.forms import BaseModelFormSet, modelformset_factory

from .models import Quiz, Question
from courses.models import Course


class QuizForm(forms.ModelForm):
    num_questions = forms.IntegerField(
        required=False,
        min_value=1,
        label='Number of random questions',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to add questions manually'}),
    )

    class Meta:
        model = Quiz
        fields = ['course', 'title', 'total_marks', 'duration_minutes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        teacher_profile = kwargs.pop('teacher_profile', None)
        super().__init__(*args, **kwargs)
        if teacher_profile is not None:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher_profile)
        else:
            self.fields['course'].queryset = Course.objects.none()
        self.fields['course'].label = 'Course'
        self.fields['title'].label = 'Quiz Title'
        self.fields['total_marks'].label = 'Total Marks'
        self.fields['duration_minutes'].label = 'Duration (minutes)'


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'text',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_choice',
            'marks',
        ]
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'option_a': forms.TextInput(attrs={'class': 'form-control'}),
            'option_b': forms.TextInput(attrs={'class': 'form-control'}),
            'option_c': forms.TextInput(attrs={'class': 'form-control'}),
            'option_d': forms.TextInput(attrs={'class': 'form-control'}),
            'correct_choice': forms.Select(attrs={'class': 'form-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class BaseQuestionFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        filled_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]

        if len(filled_forms) < 1:
            raise forms.ValidationError('Please add at least one question for the quiz.')


QuestionFormSet = modelformset_factory(
    Question,
    form=QuestionForm,
    formset=BaseQuestionFormSet,
    extra=5,
    can_delete=True,
    validate_min=True,
    min_num=1,
)


class QuizAnswerForm(forms.Form):
    def __init__(self, *args, quiz_questions=None, **kwargs):
        super().__init__(*args, **kwargs)
        quiz_questions = quiz_questions or []
        for quiz_question in quiz_questions:
            question = quiz_question.question
            field_name = f'question_{question.id}'
            self.fields[field_name] = forms.ChoiceField(
                label=question.text,
                choices=[
                    ('A', question.option_a),
                    ('B', question.option_b),
                    ('C', question.option_c),
                    ('D', question.option_d),
                ],
                widget=forms.RadioSelect,
                required=True,
            )
        self.quiz_questions = quiz_questions
