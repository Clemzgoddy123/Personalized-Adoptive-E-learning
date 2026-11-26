import random

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.decorators import student_required, teacher_required
from students.models import StudentProfile
from .forms import QuestionFormSet, QuizAnswerForm, QuizForm
from .models import Question, Quiz, QuizQuestion, QuizResult
from teachers.models import TeacherProfile


@login_required
def quiz_list(request):
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    student_profile = StudentProfile.objects.filter(user=request.user).first()
    quizzes = Quiz.objects.select_related('course').annotate(assigned_question_count=Count('quiz_questions'))

    if teacher_profile:
        quizzes = quizzes.filter(course__teacher=teacher_profile)
    elif student_profile:
        quizzes = quizzes.filter(course__enrollments__student=student_profile).distinct()

    taken_quiz_ids = []
    student_results = {}
    if student_profile:
        student_results = {
            result.quiz_id: result.score
            for result in QuizResult.objects.filter(student=student_profile)
        }
        taken_quiz_ids = list(student_results.keys())

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes': quizzes,
        'teacher_profile': teacher_profile,
        'student_profile': student_profile,
        'taken_quiz_ids': taken_quiz_ids,
        'student_results': student_results,
    })


@student_required
def student_take_quiz(request, quiz_id):
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    quiz = get_object_or_404(Quiz.objects.select_related('course'), pk=quiz_id)

    if not quiz.course.enrollments.filter(student=student_profile).exists():
        raise Http404('Quiz not available for this student.')

    quiz_questions = quiz.quiz_questions.select_related('question').all()
    if not quiz_questions:
        return render(request, 'quizzes/student_take_quiz.html', {
            'quiz': quiz,
            'message': 'This quiz has no questions yet. Please contact your teacher.',
        })

    existing_result = QuizResult.objects.filter(quiz=quiz, student=student_profile).first()
    score = None
    total_marks = quiz.total_marks

    if request.method == 'POST':
        form = QuizAnswerForm(request.POST, quiz_questions=quiz_questions)
        if form.is_valid():
            score = 0
            for quiz_question in quiz_questions:
                question = quiz_question.question
                answer = form.cleaned_data.get(f'question_{question.id}')
                if answer == question.correct_choice:
                    score += question.marks

            quiz_result, _ = QuizResult.objects.update_or_create(
                quiz=quiz,
                student=student_profile,
                defaults={'score': score},
            )
            existing_result = quiz_result

            return render(request, 'quizzes/student_take_quiz.html', {
                'quiz': quiz,
                'score': score,
                'total_marks': total_marks,
                'existing_result': existing_result,
                'student_profile': student_profile,
            })
    else:
        form = QuizAnswerForm(quiz_questions=quiz_questions)

    return render(request, 'quizzes/student_take_quiz.html', {
        'quiz': quiz,
        'form': form,
        'quiz_questions': quiz_questions,
        'existing_result': existing_result,
        'score': score,
        'total_marks': total_marks,
        'student_profile': student_profile,
    })


@login_required
def student_view_quiz_questions(request, quiz_id):
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    quiz = get_object_or_404(Quiz.objects.select_related('course'), pk=quiz_id)

    if not quiz.course.enrollments.filter(student=student_profile).exists():
        raise Http404('Quiz not available for this student.')

    quiz_questions = quiz.quiz_questions.select_related('question').all()

    return render(request, 'quizzes/student_view_quiz_questions.html', {
        'quiz': quiz,
        'quiz_questions': quiz_questions,
    })


@teacher_required
def teacher_quiz_create(request):
    teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
    if request.method == 'POST':
        num_questions = request.POST.get('num_questions')
        form = QuizForm(request.POST, teacher_profile=teacher_profile)

        if num_questions:
            question_formset = QuestionFormSet(queryset=Question.objects.none())
            if form.is_valid():
                try:
                    num_questions_value = int(num_questions)
                except (TypeError, ValueError):
                    form.add_error('num_questions', 'Enter a valid number of questions.')
                else:
                    quiz = form.save(commit=False)
                    available_questions = list(Question.objects.filter(course=quiz.course))
                    if len(available_questions) < num_questions_value:
                        form.add_error(None, f'Only {len(available_questions)} question(s) are available')
                    else:
                        quiz.save()
                        selected_questions = random.sample(available_questions, num_questions_value)
                        quiz_questions = [QuizQuestion(quiz=quiz, question=question, order=index) for index, question in enumerate(selected_questions)]
                        QuizQuestion.objects.bulk_create(quiz_questions)
                        return redirect(reverse('quiz_list'))
        else:
            question_formset = QuestionFormSet(request.POST, queryset=Question.objects.none())
            if form.is_valid() and question_formset.is_valid():
                quiz = form.save()
                quiz_questions = []
                for index, question_form in enumerate(question_formset.cleaned_data):
                    if question_form and not question_form.get('DELETE', False):
                        question = Question(
                            course=quiz.course,
                            text=question_form['text'],
                            option_a=question_form['option_a'],
                            option_b=question_form['option_b'],
                            option_c=question_form['option_c'],
                            option_d=question_form['option_d'],
                            correct_choice=question_form['correct_choice'],
                            marks=question_form['marks'],
                        )
                        question.save()
                        quiz_questions.append(QuizQuestion(quiz=quiz, question=question, order=index))
                if not quiz_questions:
                    form.add_error(None, 'Please add at least one question to create the quiz.')
                else:
                    QuizQuestion.objects.bulk_create(quiz_questions)
                    return redirect(reverse('quiz_list'))
    else:
        form = QuizForm(teacher_profile=teacher_profile)
        question_formset = QuestionFormSet(queryset=Question.objects.none())

    return render(request, 'quizzes/teacher_quiz_create.html', {
        'form': form,
        'question_formset': question_formset,
        'teacher_profile': teacher_profile,
    })
