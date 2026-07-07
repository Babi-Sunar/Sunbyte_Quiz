import random
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ChoiceFormSet, EmailLoginForm, JoinSessionForm, QuestionForm,
    SessionSettingsForm, SignUpForm, TrueFalseAnswerForm,
)
from .models import Choice, Participant, Question, QuizSession, Response


# =======================================================================
# Auth & landing
# =======================================================================
def home(request):
    return render(request, 'quizapp/home.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('quizapp:dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to SunByte Quiz, {user.username}!')
            return redirect('quizapp:dashboard')
    else:
        form = SignUpForm()

    return render(request, 'quizapp/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('quizapp:dashboard')

    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                user_obj = None

            user = None
            if user_obj is not None:
                user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)
                if not form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)
                return redirect('quizapp:dashboard')
            messages.error(request, 'Invalid email or password.')
    else:
        form = EmailLoginForm()

    return render(request, 'quizapp/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('quizapp:home')


@login_required
def dashboard(request):
    hosted_sessions = QuizSession.objects.filter(host=request.user)[:10]
    joined_sessions = Participant.objects.filter(user=request.user).select_related('session')[:10]
    return render(request, 'quizapp/dashboard.html', {
        'hosted_sessions': hosted_sessions,
        'joined_sessions': joined_sessions,
    })


# =======================================================================
# Helpers
# =======================================================================
def _participant_session_key(session):
    return f'participant_id_{session.id}'


def get_current_participant(request, session):
    """Find the Participant record for whoever is looking at this
    session right now — a logged-in user OR a guest tracked via the
    Django session (works without any login)."""
    pid = request.session.get(_participant_session_key(session))
    if pid:
        participant = Participant.objects.filter(id=pid, session=session).first()
        if participant:
            return participant
    if request.user.is_authenticated:
        return Participant.objects.filter(session=session, user=request.user).first()
    return None


# =======================================================================
# Joining a session — no account required
# =======================================================================
def join_session(request):
    prefill_code = request.GET.get('code', '')

    if request.method == 'POST':
        form = JoinSessionForm(request.POST, user_is_authenticated=request.user.is_authenticated)
        if form.is_valid():
            code = form.cleaned_data['code']
            session = QuizSession.objects.filter(code=code).first()

            if session is None:
                messages.error(request, 'No session found with that code.')
            elif session.status == 'ended':
                messages.error(request, 'This session has already ended.')
            else:
                participant = get_current_participant(request, session)
                if participant is None:
                    if request.user.is_authenticated:
                        participant, _ = Participant.objects.get_or_create(session=session, user=request.user)
                    else:
                        participant = Participant.objects.create(
                            session=session,
                            guest_name=form.cleaned_data['display_name'].strip(),
                        )
                request.session[_participant_session_key(session)] = participant.id
                return redirect('quizapp:session_room', code=session.code)
    else:
        form = JoinSessionForm(
            initial={'code': prefill_code},
            user_is_authenticated=request.user.is_authenticated,
        )

    return render(request, 'quizapp/join_session.html', {'form': form})


# =======================================================================
# Session builder (host only)
# =======================================================================
@login_required
def create_session(request):
    if request.method == 'POST':
        form = SessionSettingsForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.host = request.user
            session.save()
            messages.success(request, 'Session created! Now add some questions.')
            return redirect('quizapp:manage_session', code=session.code)
    else:
        form = SessionSettingsForm()

    return render(request, 'quizapp/create_session.html', {'form': form})


def _get_hosted_session_or_404(request, code):
    return get_object_or_404(QuizSession, code=code, host=request.user)


@login_required
def manage_session(request, code):
    session = _get_hosted_session_or_404(request, code)
    questions = session.questions.all()
    join_url = request.build_absolute_uri(f'/session/join/?code={session.code}')
    return render(request, 'quizapp/manage_session.html', {
        'session': session,
        'questions': questions,
        'join_url': join_url,
    })


@login_required
def add_question(request, code):
    session = _get_hosted_session_or_404(request, code)
    next_order = session.questions.count() + 1

    question_type = request.POST.get('question_type', 'mcq')
    formset = None
    tf_form = None

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                question = form.save(commit=False)
                question.session = session
                question.order = next_order
                question.save()

                if question.question_type == 'true_false':
                    tf_form = TrueFalseAnswerForm(request.POST)
                    if tf_form.is_valid():
                        correct = tf_form.cleaned_data['correct_answer']
                        Choice.objects.create(question=question, text='True', is_correct=(correct == 'true'), order=1)
                        Choice.objects.create(question=question, text='False', is_correct=(correct == 'false'), order=2)
                        messages.success(request, 'Question added.')
                        return redirect('quizapp:manage_session', code=session.code)
                    question.delete()
                else:
                    formset = ChoiceFormSet(request.POST, request.FILES, instance=question)
                    if formset.is_valid():
                        choices = formset.save(commit=False)
                        if not any(c.is_correct for c in choices):
                            messages.error(request, 'Mark at least one option as the correct answer.')
                        else:
                            for i, choice in enumerate(choices, start=1):
                                choice.order = i
                                choice.save()
                            messages.success(request, 'Question added.')
                            return redirect('quizapp:manage_session', code=session.code)
                    question.delete()
    else:
        form = QuestionForm()

    if formset is None:
        formset = ChoiceFormSet()
    if tf_form is None:
        tf_form = TrueFalseAnswerForm()

    return render(request, 'quizapp/question_form.html', {
        'session': session,
        'form': form,
        'formset': formset,
        'tf_form': tf_form,
    })


@login_required
def delete_question(request, code, question_id):
    session = _get_hosted_session_or_404(request, code)
    question = get_object_or_404(Question, id=question_id, session=session)
    if request.method == 'POST':
        question.delete()
        messages.info(request, 'Question removed.')
    return redirect('quizapp:manage_session', code=session.code)


@login_required
def publish_session(request, code):
    session = _get_hosted_session_or_404(request, code)
    if session.questions.count() == 0:
        messages.error(request, 'Add at least one question before going live.')
    else:
        session.status = 'active'
        session.save(update_fields=['status'])
        messages.success(request, f'Session is live! Share code {session.code}.')
    return redirect('quizapp:manage_session', code=session.code)


@login_required
def end_session(request, code):
    session = _get_hosted_session_or_404(request, code)
    session.status = 'ended'
    session.save(update_fields=['status'])
    session.recompute_ranks()
    messages.info(request, 'Session ended.')
    return redirect('quizapp:manage_session', code=session.code)


# =======================================================================
# Lobby / taking the quiz / results
# =======================================================================
def session_room(request, code):
    session = get_object_or_404(QuizSession, code=code)
    is_host = request.user.is_authenticated and session.host_id == request.user.id
    participant = get_current_participant(request, session)

    if not is_host and participant is None:
        return redirect(f"/session/join/?code={session.code}")

    if participant is not None and participant.submitted:
        return redirect('quizapp:result_detail', code=session.code)

    return render(request, 'quizapp/session_room.html', {
        'session': session,
        'is_host': is_host,
        'participant': participant,
        'participants': session.participants.all(),
    })


def take_quiz(request, code):
    session = get_object_or_404(QuizSession, code=code)
    participant = get_current_participant(request, session)

    if participant is None:
        return redirect(f"/session/join/?code={session.code}")
    if session.status != 'active':
        messages.info(request, 'This quiz is not live yet.')
        return redirect('quizapp:session_room', code=session.code)
    if participant.submitted:
        return redirect('quizapp:result_detail', code=session.code)

    questions = list(session.questions.prefetch_related('choices').all())
    if session.shuffle_questions:
        rng = random.Random(participant.id)
        rng.shuffle(questions)

    if request.method == 'POST':
        correct_count = 0
        wrong_count = 0
        not_attempted_count = 0
        total_marks = Decimal('0')

        for question in questions:
            field_name = f'answer_{question.id}'
            choice_id = request.POST.get(field_name)
            selected_choice = None
            if choice_id:
                selected_choice = next((c for c in question.choices.all() if str(c.id) == str(choice_id)), None)

            marks = question.effective_marks()
            if selected_choice is None:
                is_correct = False
                marks_awarded = Decimal('0')
                not_attempted_count += 1
            elif selected_choice.is_correct:
                is_correct = True
                marks_awarded = marks
                correct_count += 1
            else:
                is_correct = False
                marks_awarded = -session.negative_marks if session.negative_marking else Decimal('0')
                wrong_count += 1

            total_marks += marks_awarded

            Response.objects.update_or_create(
                participant=participant, question=question,
                defaults={
                    'selected_choice': selected_choice,
                    'is_correct': is_correct,
                    'marks_awarded': marks_awarded,
                },
            )

        participant.submitted = True
        participant.submitted_at = timezone.now()
        participant.total_marks = total_marks
        participant.correct_count = correct_count
        participant.wrong_count = wrong_count
        participant.not_attempted_count = not_attempted_count
        participant.save()

        session.recompute_ranks()
        return redirect('quizapp:result_detail', code=session.code)

    total_seconds = None
    if session.timer_mode == 'per_quiz':
        total_seconds = session.total_time_minutes * 60

    return render(request, 'quizapp/take_quiz.html', {
        'session': session,
        'participant': participant,
        'questions': questions,
        'total_seconds': total_seconds,
    })


def result_detail(request, code):
    session = get_object_or_404(QuizSession, code=code)
    participant = get_current_participant(request, session)

    if participant is None or not participant.submitted:
        messages.info(request, 'Attempt this quiz first to see your result.')
        return redirect('quizapp:session_room', code=session.code)

    leaderboard = session.participants.filter(submitted=True).order_by('-total_marks', 'submitted_at')
    responses = participant.responses.select_related('question', 'selected_choice')

    return render(request, 'quizapp/result_detail.html', {
        'session': session,
        'participant': participant,
        'leaderboard': leaderboard,
        'responses': responses,
        'total_possible': session.total_possible_marks(),
    })
