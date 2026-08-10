import email
import random
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from requests import session

from .forms import (
    ChoiceFormSet, EmailLoginForm, JoinSessionForm, QuestionForm,
    SessionSettingsForm, SignUpForm, TrueFalseAnswerForm,
)
from .models import Choice, Participant, Question, QuizSession, Response, Category

import cloudinary.uploader
from io import BytesIO
# =======================================================================
# Auth & landing
# =======================================================================
import resend

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

def signup_view(request):

    if request.user.is_authenticated:
        return redirect('quizapp:dashboard')

    if request.method == 'POST':

        form = SignUpForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            # User cannot log in until email is verified
            user.is_active = False
            user.save()

            # Generate verification token
            uid = urlsafe_base64_encode(
                force_bytes(user.pk)
            )

            token = default_token_generator.make_token(user)

            verification_url = request.build_absolute_uri(
                reverse(
                    'quizapp:verify_email',
                    kwargs={
                        'uidb64': uid,
                        'token': token,
                    }
                )
            )

            try:

                send_verification_email(
                    user,
                    verification_url
                )

            except Exception as e:

                # Remove account if email could not be sent
                user.delete()

                messages.error(
                    request,
                    'We could not send the verification email. Please try again.'
                )

                print("Resend error:", e)

                return render(
                    request,
                    'quizapp/signup.html',
                    {'form': form}
                )

            messages.success(
                request,
                'Account created! Please check your email and verify your account before logging in.'
            )

            return redirect('quizapp:login')

        else:
            print(form.errors)

    else:
        form = SignUpForm()

    return render(
        request,
        'quizapp/signup.html',
        {'form': form}
    )
# from django.http import HttpResponse

# def signup_view(request):
#     if request.method == "POST":
#         return HttpResponse("Form submitted!")

#     return render(request, "quizapp/signup.html")
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('quizapp:dashboard')

    if request.method == 'POST':
        form = EmailLoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user_obj = User.objects.filter(
                email__iexact=email
            ).first()

            if user_obj is not None and not user_obj.is_active:

                # Check email verification first
                if not user_obj.is_active:
                    messages.error(
                        request,
                        'Please verify your email address before logging in.'
                    )
                    return render(
                        request,
                        'quizapp/login.html',
                        {'form': form}
                    )

                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password
                )

                if user is not None:
                    login(request, user)

                    if not form.cleaned_data.get('remember_me'):
                        request.session.set_expiry(0)

                    return redirect('quizapp:dashboard')

            messages.error(
                request,
                'Invalid email or password.'
            )

    else:
        form = EmailLoginForm()

    return render(
        request,
        'quizapp/login.html',
        {'form': form}
    )


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('quizapp:login')

@never_cache
@login_required(login_url='quizapp:login')
def dashboard(request):
    hosted_sessions = QuizSession.objects.filter(host=request.user)[:10]
    joined_sessions = Participant.objects.filter(user=request.user).select_related('session')[:10]
    return render(request, 'quizapp/user_dashboard.html', {
        'hosted_sessions': hosted_sessions,
        'joined_sessions': joined_sessions,
    })


# email verification view
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode

User = get_user_model()


def verify_email_view(request, uidb64, token):

    try:

        uid = urlsafe_base64_decode(uidb64).decode()

        user = User.objects.get(pk=uid)

    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist
    ):

        user = None

    if user is not None:

        if default_token_generator.check_token(
            user,
            token
        ):

            user.is_active = True

            user.save(
                update_fields=['is_active']
            )

            messages.success(
                request,
                'Your email has been verified successfully. You can now log in.'
            )

            return redirect('quizapp:login')

    return render(
        request,
        'quizapp/email_verification_invalid.html'
    )
    
# helper fo verification email
import resend

from django.conf import settings
def send_verification_email(user, verification_url):
    resend.api_key = settings.RESEND_API_KEY

    resend.Emails.send({
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [user.email],
        "subject": "Verify your SunByte Quiz account",
        "html": f"""
            <div style="
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: auto;
                padding: 30px;
                background: #f7f7f7;
            ">

                <div style="
                    background: #FFC300;
                    padding: 20px;
                    text-align: center;
                    border-radius: 12px 12px 0 0;
                ">
                    <h1 style="margin: 0; color: #111;">
                        SunByte Quiz
                    </h1>
                </div>

                <div style="
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 12px 12px;
                ">

                    <h2>Verify your email</h2>

                    <p>
                        Hello <strong>{user.username}</strong>,
                    </p>

                    <p>
                        Thank you for creating your SunByte Quiz account.
                        Please verify your email address to activate your account.
                    </p>

                    <div style="text-align: center; margin: 30px 0;">

                        <a href="{verification_url}"
                           style="
                               display: inline-block;
                               padding: 14px 25px;
                               background: #FFC300;
                               color: #111;
                               text-decoration: none;
                               font-weight: bold;
                               border-radius: 8px;
                           ">
                            Verify My Email
                        </a>

                    </div>

                    <p>
                        If you did not create this account, you can safely
                        ignore this email.
                    </p>

                    <p style="font-size: 13px; color: #777;">
                        This is an automated email from SunByte Quiz.
                    </p>

                </div>

            </div>
        """
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
@never_cache
@login_required
def create_session(request):
    categories = Category.objects.all()
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

    return render(
        request,
        "quizapp/create_session.html",
        {
            "form": form,
            "categories": categories,
        },)


def _get_hosted_session_or_404(request, code):
    return get_object_or_404(QuizSession, code=code, host=request.user)



# manage session
import os
import qrcode
from django.conf import settings
import base64
import io
@never_cache
@login_required
def manage_session(request, code):
    session = _get_hosted_session_or_404(request, code)
    questions = session.questions.all()

    join_url = request.build_absolute_uri(
        f"/session/join/?code={session.code}"
    )

    # Generate QR code in memory
    qr = qrcode.make(join_url)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    qr_image = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return render(
        request,
        "quizapp/manage_session.html",
        {
            "session": session,
            "questions": questions,
            "join_url": join_url,
            "qr_image": qr_image,
        },
    )


@never_cache
@login_required
def add_question(request, code):
    session = _get_hosted_session_or_404(request, code)

    last_question = session.questions.order_by("-order").first()
    next_order = (
        1 if last_question is None
        else last_question.order + 1
    )

    formset = None
    tf_form = None

    if request.method == "POST":

        print("\n========== POST RECEIVED ==========\n")

        # Question form
        # request.FILES is still passed because images may be uploaded.
        form = QuestionForm(request.POST, request.FILES)

        if form.is_valid():

            print("✓ Question form is valid")

            with transaction.atomic():

                # ----------------------------------
                # Create question object
                # ----------------------------------

                question = form.save(commit=False)
                question.session = session
                question.order = next_order

                # ----------------------------------
                # Save question
                # ----------------------------------

                try:

                    print("=== SAVING QUESTION ===")

                    question.save()

                    print("=== QUESTION SAVED ===")

                except Exception as e:

                    print("=== QUESTION SAVE ERROR ===")
                    print(type(e).__name__)
                    print(str(e))

                    raise

                # ==================================
                # TRUE / FALSE
                # ==================================

                if question.question_type == "true_false":

                    tf_form = TrueFalseAnswerForm(request.POST)

                    if tf_form.is_valid():

                        print("✓ True/False form is valid")

                        correct = tf_form.cleaned_data[
                            "correct_answer"
                        ]

                        Choice.objects.create(
                            question=question,
                            text="True",
                            is_correct=(correct == "true"),
                            order=1,
                        )

                        Choice.objects.create(
                            question=question,
                            text="False",
                            is_correct=(correct == "false"),
                            order=2,
                        )

                        messages.success(
                            request,
                            "Question added successfully."
                        )

                        return redirect(
                            "quizapp:manage_session",
                            code=session.code,
                        )

                    else:

                        print("True/False Errors:")
                        print(tf_form.errors)

                        question.delete()

                # ==================================
                # MCQ
                # ==================================

                else:

                    formset = ChoiceFormSet(
                        request.POST,
                        request.FILES,
                        instance=question,
                    )

                    if formset.is_valid():

                        print("✓ Choice Formset is valid")

                        choices = formset.save(commit=False)

                        valid_choices = [
                            c
                            for c in choices
                            if (
                                (c.text and c.text.strip())
                                or c.image
                            )
                        ]

                        print(
                            f"Choices received: "
                            f"{len(valid_choices)}"
                        )

                        # ----------------------------------
                        # At least two choices
                        # ----------------------------------

                        if len(valid_choices) < 2:

                            print(
                                "ERROR: Less than two choices."
                            )

                            messages.error(
                                request,
                                "Please provide at least two options.",
                            )

                            question.delete()

                        # ----------------------------------
                        # Correct answer required
                        # ----------------------------------

                        elif not any(
                            c.is_correct
                            for c in valid_choices
                        ):

                            print(
                                "ERROR: No correct answer selected."
                            )

                            messages.error(
                                request,
                                "Please select one correct answer.",
                            )

                            question.delete()

                        # ----------------------------------
                        # Save choices
                        # ----------------------------------

                        else:

                            for i, choice in enumerate(
                                valid_choices,
                                start=1
                            ):

                                choice.question = question
                                choice.order = i
                                choice.save()

                            print(
                                "✓ Question saved successfully"
                            )

                            messages.success(
                                request,
                                "Question added successfully.",
                            )

                            return redirect(
                                "quizapp:manage_session",
                                code=session.code,
                            )

                    else:

                        print(
                            "\n========== FORMSET ERRORS =========="
                        )

                        print(formset.errors)
                        print(formset.non_form_errors())

                        print(
                            "====================================\n"
                        )

                        question.delete()

        else:

            print(
                "\n========== QUESTION FORM ERRORS =========="
            )

            print(form.errors)

            print(
                "==========================================\n"
            )

    else:

        form = QuestionForm()

    # ----------------------------------
    # Prepare empty forms for GET/render
    # ----------------------------------

    if formset is None:
        formset = ChoiceFormSet()

    if tf_form is None:
        tf_form = TrueFalseAnswerForm()

    return render(
        request,
        "quizapp/question_form.html",
        {
            "session": session,
            "form": form,
            "formset": formset,
            "tf_form": tf_form,
        },
    )


@never_cache
@login_required
def delete_question(request, code, question_id):
    session = _get_hosted_session_or_404(request, code)

    question = get_object_or_404(
        Question,
        id=question_id,
        session=session,
    )

    if request.method == "POST":

        question.delete()

        # Reorder remaining questions
        questions = session.questions.order_by("order")

        for index, q in enumerate(questions, start=1):
            if q.order != index:
                q.order = index
                q.save(update_fields=["order"])

        messages.success(request, "Question deleted successfully.")

        return redirect(
            "quizapp:manage_session",
            code=session.code,
        )

    return render(
        request,
        "quizapp/delete_question.html",
        {
            "session": session,
            "question": question,
        },
    )

@never_cache
@login_required
def edit_question(request, code, question_id):

    session = _get_hosted_session_or_404(request, code)

    question = get_object_or_404(
        Question,
        id=question_id,
        session=session,
    )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        form = QuestionForm(
            request.POST,
            request.FILES,
            instance=question,
        )

        # =================================================
        # QUESTION FORM INVALID
        # =================================================

        if not form.is_valid():

            formset = ChoiceFormSet(
                request.POST,
                request.FILES,
                instance=question,
            )

            tf_form = TrueFalseAnswerForm(request.POST)

            return render(
                request,
                "quizapp/edit_question.html",
                {
                    "session": session,
                    "question": question,
                    "form": form,
                    "formset": formset,
                    "tf_form": tf_form,
                },
            )

        # =================================================
        # NEW QUESTION TYPE
        # =================================================

        new_question_type = form.cleaned_data["question_type"]

        # =====================================================
        # TRUE / FALSE
        # =====================================================

        if new_question_type == "true_false":

            tf_form = TrueFalseAnswerForm(request.POST)

            if tf_form.is_valid():

                # Save question first
                question = form.save()

                correct = tf_form.cleaned_data[
                    "correct_answer"
                ]

                # Get existing choices
                choices = list(
                    question.choices.order_by("order")
                )

                # ---------------------------------------------
                # EXISTING CHOICES AVAILABLE
                # ---------------------------------------------

                if len(choices) >= 2:

                    true_choice = choices[0]
                    false_choice = choices[1]

                    true_choice.text = "True"
                    true_choice.order = 1
                    true_choice.is_correct = (
                        correct == "true"
                    )
                    true_choice.save()

                    false_choice.text = "False"
                    false_choice.order = 2
                    false_choice.is_correct = (
                        correct == "false"
                    )
                    false_choice.save()

                    # Remove extra choices
                    if len(choices) > 2:

                        Choice.objects.filter(
                            question=question
                        ).exclude(
                            id__in=[
                                true_choice.id,
                                false_choice.id,
                            ]
                        ).delete()

                # ---------------------------------------------
                # NO EXISTING CHOICES
                # ---------------------------------------------

                else:

                    # Remove anything that may exist
                    Choice.objects.filter(
                        question=question
                    ).delete()

                    Choice.objects.create(
                        question=question,
                        text="True",
                        order=1,
                        is_correct=(
                            correct == "true"
                        ),
                    )

                    Choice.objects.create(
                        question=question,
                        text="False",
                        order=2,
                        is_correct=(
                            correct == "false"
                        ),
                    )

                messages.success(
                    request,
                    "Question updated successfully."
                )

                return redirect(
                    "quizapp:manage_session",
                    code=session.code,
                )

            # ---------------------------------------------
            # TRUE/FALSE FORM INVALID
            # ---------------------------------------------

            formset = ChoiceFormSet(
                instance=question
            )

            return render(
                request,
                "quizapp/edit_question.html",
                {
                    "session": session,
                    "question": question,
                    "form": form,
                    "formset": formset,
                    "tf_form": tf_form,
                },
            )

        # =====================================================
        # MULTIPLE CHOICE
        # =====================================================

        else:

            formset = ChoiceFormSet(
                request.POST,
                request.FILES,
                instance=question,
            )

            tf_form = TrueFalseAnswerForm()

            # ---------------------------------------------
            # FORMSET VALIDATION
            # ---------------------------------------------

            if formset.is_valid():

                # Check that there is exactly one correct answer
                correct_count = sum(
                    1
                    for choice in formset
                    if choice.cleaned_data
                    and choice.cleaned_data.get(
                        "is_correct"
                    )
                )

                if correct_count == 0:

                    messages.error(
                        request,
                        "Please select one correct answer."
                    )

                    return render(
                        request,
                        "quizapp/edit_question.html",
                        {
                            "session": session,
                            "question": question,
                            "form": form,
                            "formset": formset,
                            "tf_form": tf_form,
                        },
                    )

                if correct_count > 1:

                    messages.error(
                        request,
                        "Please select only one correct answer."
                    )

                    return render(
                        request,
                        "quizapp/edit_question.html",
                        {
                            "session": session,
                            "question": question,
                            "form": form,
                            "formset": formset,
                            "tf_form": tf_form,
                        },
                    )

                # -----------------------------------------
                # SAVE QUESTION
                # -----------------------------------------

                question = form.save()

                # -----------------------------------------
                # SAVE FORMSET
                # -----------------------------------------

                choices = formset.save(
                    commit=False
                )

                # IDs of submitted existing choices
                submitted_choice_ids = [
                    choice.id
                    for choice in choices
                    if choice.id
                ]

                # -----------------------------------------
                # DELETE REMOVED CHOICES
                # -----------------------------------------

                Choice.objects.filter(
                    question=question
                ).exclude(
                    id__in=submitted_choice_ids
                ).delete()

                # -----------------------------------------
                # SAVE EACH CHOICE
                # -----------------------------------------

                for index, choice in enumerate(
                    choices,
                    start=1
                ):

                    choice.question = question

                    choice.order = index

                    choice.save()

                # -----------------------------------------
                # PROCESS CHOICE IMAGE REMOVAL
                # -----------------------------------------

                for choice in choices:

                    if not choice.id:
                        continue

                    remove_flag = request.POST.get(
                        f"remove_choice_image_{choice.id}"
                    )

                    if remove_flag == "1":

                        if choice.image:

                            choice.image.delete(
                                save=False
                            )

                        choice.image = None

                        choice.save(
                            update_fields=["image"]
                        )

                # -----------------------------------------
                # PROCESS QUESTION IMAGE REMOVAL
                # -----------------------------------------

                remove_question_image = request.POST.get(
                    "remove_question_image"
                )

                if remove_question_image == "1":

                    if question.image:

                        question.image.delete(
                            save=False
                        )

                    question.image = None

                    question.save(
                        update_fields=["image"]
                    )

                messages.success(
                    request,
                    "Question updated successfully."
                )

                return redirect(
                    "quizapp:manage_session",
                    code=session.code,
                )

    # =====================================================
    # GET
    # =====================================================

    else:

        form = QuestionForm(
            instance=question
        )

        # Always provide MCQ formset.
        # This allows:
        #
        # T/F -> MCQ
        #
        # switching.

        formset = ChoiceFormSet(
            instance=question
        )

        # ---------------------------------------------
        # TRUE / FALSE
        # ---------------------------------------------

        if question.question_type == "true_false":

            correct = "true"

            for choice in question.choices.all():

                if choice.is_correct:

                    if (
                        choice.text.lower()
                        == "false"
                    ):
                        correct = "false"

                    else:
                        correct = "true"

            tf_form = TrueFalseAnswerForm(
                initial={
                    "correct_answer": correct
                }
            )

        # ---------------------------------------------
        # MCQ
        # ---------------------------------------------

        else:

            tf_form = TrueFalseAnswerForm()

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "quizapp/edit_question.html",
        {
            "session": session,
            "question": question,
            "form": form,
            "formset": formset,
            "tf_form": tf_form,
        },
    )


@never_cache
@login_required
def publish_session(request, code):

    session = _get_hosted_session_or_404(request, code)

    if request.method == "POST":

        if session.question_count == 0:

            messages.error(
                request,
                "Add at least one question before publishing the session."
            )

            return redirect(
                "quizapp:manage_session",
                code=session.code,
            )


        # Clear previous participants when starting a fresh session
        session.participants.all().delete()


        # Reset session state
        session.status = "active"
        session.current_question = 0
        session.quiz_state = "waiting"

        # Reset timers
        session.question_started_at = None
        session.quiz_started_at = None


        session.save(
            update_fields=[
                "status",
                "current_question",
                "quiz_state",
                "question_started_at",
                "quiz_started_at",
            ]
        )


        messages.success(
            request,
            "Session published successfully. Participants can now join using the session code or QR code."
        )


        return redirect(
            "quizapp:host_room",
            code=session.code,
        )


    return render(
        request,
        "quizapp/publish_session.html",
        {
            "session": session,
        },
    )

@never_cache
@login_required
def end_session(request, code):

    session = _get_hosted_session_or_404(request, code)


    if request.method == "POST":

        session.status = 'ended'

        session.save(update_fields=['status'])
        session.recompute_ranks()

        messages.info(request, 'Session ended.')

        return redirect(
            'quizapp:manage_session',
            code=session.code
        )


    return render(
        request,
        'quizapp/end_session.html',
        {
            'session': session
        }
    )

# my quizes
@login_required
def my_quizzes(request):

    quizzes = QuizSession.objects.filter(
        host=request.user
    ).order_by('-created_at')


    return render(
        request,
        'quizapp/my_quizzes.html',
        {
            'quizzes': quizzes
        }
    )

# delete session 
@login_required
def delete_session(request, code):
    session = get_object_or_404(QuizSession, code=code)

    if session.status == "live":
        messages.error(request, "End the session before deleting it.")
        return redirect("quizapp:manage_session", code=code)

    session.delete()

    messages.success(request, "Session deleted successfully.")
    return redirect("quizapp:dashboard")

from django.db.models import Avg, Max
@login_required
def session_results(request, code):
    session = get_object_or_404(QuizSession, code=code)

    participants = session.participants.filter(
        submitted=True
    ).order_by(
        "-total_marks",
        "submitted_at"
    )

    stats = participants.aggregate(
        highest_score=Max("total_marks"),
        average_score=Avg("total_marks"),
    )

    context = {
        "session": session,
        "participants": participants,
        "highest_score": stats["highest_score"] or 0,
        "average_score": round(stats["average_score"], 2) if stats["average_score"] else 0,
    }

    return render(request, "quizapp/session_results.html", context)

# host session room
import base64
import io
import qrcode


@never_cache
@login_required
def host_room(request, code):

    session = _get_hosted_session_or_404(request, code)

    join_url = request.build_absolute_uri(
        f"/session/join/?code={session.code}"
    )

    # Generate QR code in memory
    qr = qrcode.make(join_url)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    qr_image = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    context = {
        "session": session,
        "qr_image": qr_image,
    }

    return render(
        request,
        "quizapp/hostSession_room.html",
        context,
    )

@login_required
def participant_count(request, code):
    session = _get_hosted_session_or_404(request, code)

    return JsonResponse({
        "count": session.player_count
    })
    
@never_cache
@login_required
def start_quiz(request, code):

    session = _get_hosted_session_or_404(request, code)

    if request.method == "POST":

        if session.status != "active":
            messages.error(
                request,
                "Session is not active."
            )

            return redirect(
                "quizapp:final_room",
                code=session.code,
            )


        session.quiz_state = "running"


        # Start timer depending on mode

        if session.timer_mode == "per_question":

            session.question_started_at = timezone.now()


        elif session.timer_mode == "per_quiz":

            session.quiz_started_at = timezone.now()


        session.save()


        messages.success(
            request,
            "Quiz started successfully."
        )


    return redirect(
        "quizapp:final_room",
        code=code
    )

from django.utils import timezone


@login_required
def final_room(request, code):
    session = _get_hosted_session_or_404(request, code)

    questions = list(
        session.questions.prefetch_related("choices").order_by("order")
    )

    current_question = None
    current_question_number = 0
    question_time = None
    remaining_time = None

    if questions and 0 <= session.current_question < len(questions):

        current_question = questions[session.current_question]

        # Display number (Question 1, Question 2...)
        current_question_number = session.current_question + 1


        # ==========================
        # TIMER HANDLING
        # ==========================

        if session.timer_mode == "per_question":

            question_time = (
                current_question.time_limit_seconds
                or session.default_time_per_question_seconds
            )

            remaining_time = question_time

            if session.question_started_at:

                elapsed = (
                    timezone.now() - session.question_started_at
                ).total_seconds()

                remaining_time = max(
                    0,
                    int(question_time - elapsed)
                )


        elif session.timer_mode == "none":

            # No timer mode
            question_time = None
            remaining_time = None


        elif session.timer_mode == "per_quiz":

            # Whole quiz timer (minutes → seconds)

            question_time = int(
                session.total_time_minutes * 60
            )

            remaining_time = question_time


            if session.quiz_started_at:

                elapsed = (
                    timezone.now() - session.quiz_started_at
                ).total_seconds()


                remaining_time = max(
                    0,
                    int(question_time - elapsed)
                )


    return render(
        request,
        "quizapp/finalHost_room.html",
        {
            "session": session,
            "current_question": current_question,
            "current_question_number": current_question_number,
            "question_time": question_time,
            "remaining_time": remaining_time,
        },
    )
    
    
@never_cache
@login_required
def pause_quiz(request, code):

    session = _get_hosted_session_or_404(request, code)

    if request.method == "POST":

        if session.quiz_state == "running":

            session.quiz_state = "paused"

            session.save(
                update_fields=[
                    "quiz_state",
                ]
            )

            messages.success(
                request,
                "Quiz paused."
            )

    return redirect(
        "quizapp:final_room",
        code=session.code,
    )
    
@never_cache
@login_required
def resume_quiz(request, code):

    session = _get_hosted_session_or_404(request, code)

    if request.method == "POST":

        if session.quiz_state == "paused":

            session.quiz_state = "running"

            session.save(
                update_fields=[
                    "quiz_state",
                ]
            )

            messages.success(
                request,
                "Quiz resumed."
            )

    return redirect(
        "quizapp:final_room",
        code=session.code,
    )
    
    
from django.utils import timezone

@never_cache
@login_required
def next_question(request, code):

    print("NEXT QUESTION VIEW CALLED")

    session = _get_hosted_session_or_404(request, code)

    if request.method == "POST":

        if session.quiz_state != "running":
            messages.error(
                request,
                "Start the quiz before moving to questions."
            )

            return redirect(
                "quizapp:final_room",
                code=session.code,
            )

        total_questions = session.question_count

        print("CURRENT:", session.current_question)
        print("TOTAL:", total_questions)

        if session.current_question < total_questions - 1:

            session.current_question += 1
            session.question_started_at = timezone.now()

            print("NEXT QUESTION VALUE:", session.current_question)

            session.save(
                update_fields=[
                    "current_question",
                    "question_started_at",
                ]
            )

            messages.success(
                request,
                f"Question {session.current_question + 1} started."
            )

        else:

            session.quiz_state = "finished"

            session.save(
                update_fields=[
                    "quiz_state",
                ]
            )

            messages.success(
                request,
                "Quiz finished."
            )

    return redirect(
        "quizapp:final_room",
        code=session.code,
    )

@never_cache
@login_required
def check_question_timer(request, code):

    session = _get_hosted_session_or_404(request, code)

    if session.quiz_state != "running":
        return JsonResponse({
            "status": "not_running"
        })


    # ==========================
    # NO TIMER MODE
    # ==========================
    if session.timer_mode == "none":

        return JsonResponse({
            "changed": False
        })


    # ==========================
    # WHOLE QUIZ TIMER MODE
    # ==========================
    if session.timer_mode == "per_quiz":

        if not session.quiz_started_at:
            return JsonResponse({
                "changed": False
            })


        total_seconds = int(
            session.total_time_minutes * 60
        )


        elapsed = (
            timezone.now() - session.quiz_started_at
        ).total_seconds()


        if elapsed >= total_seconds:

            session.quiz_state = "finished"

            session.save(
                update_fields=[
                    "quiz_state",
                ]
            )

            return JsonResponse({
                "finished": True
            })


        return JsonResponse({
            "changed": False
        })


    # ==========================
    # PER QUESTION TIMER MODE
    # ==========================
    if session.timer_mode == "per_question":

        questions = list(
            session.questions.order_by("order")
        )


        if not questions:
            return JsonResponse({
                "changed": False
            })


        current_question = questions[
            session.current_question
        ]


        question_time = (
            current_question.time_limit_seconds
            or session.default_time_per_question_seconds
        )


        if not session.question_started_at:
            return JsonResponse({
                "changed": False
            })


        elapsed = (
            timezone.now() - session.question_started_at
        ).total_seconds()


        if elapsed >= question_time:


            if session.current_question < len(questions) - 1:

                session.current_question += 1

                session.question_started_at = timezone.now()

                session.save(
                    update_fields=[
                        "current_question",
                        "question_started_at",
                    ]
                )


                return JsonResponse({
                    "changed": True
                })


            else:

                session.quiz_state = "finished"

                session.save(
                    update_fields=[
                        "quiz_state",
                    ]
                )


                return JsonResponse({
                    "finished": True
                })


    return JsonResponse({
        "changed": False
    })
    # NOt used
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
        return redirect(
            'quizapp:result_detail',
            code=session.code
        )

    return render(
        request,
        'quizapp/session_room.html',
        {
            'session': session,
            'is_host': is_host,
            'participant': participant,
            'participants': session.participants.all(),
        }
    )


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

    questions = list(
        session.questions
        .prefetch_related("choices")
        .order_by("order")
    )

    current_question = None

    if questions and 0 <= session.current_question < len(questions):
        current_question = questions[session.current_question]
    
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

    question_time = None
    remaining_time = 0

    if current_question:

        question_time = (
            current_question.time_limit_seconds
            or session.default_time_per_question_seconds
        )

        if session.timer_mode == "per_question":

            if session.question_started_at:

                elapsed = (
                    timezone.now() -
                    session.question_started_at
                ).total_seconds()

                remaining_time = max(
                    0,
                    int(question_time - elapsed)
                )

            else:

                remaining_time = question_time
    return render(request, 'quizapp/take_quiz.html', {
        'session': session,
        'participant': participant,
        "current_question": current_question,
        "question_time": question_time,
        "remaining_time": remaining_time,
        'total_seconds': total_seconds,
    })


# live update of participant name
def participant_list(request, code):

    session = get_object_or_404(QuizSession, code=code)

    participants = list(

        session.participants.values(
            "display_name"
        )

    )

    return JsonResponse({

        "participants": participants

    })
def quiz_status(request, code):

    session = get_object_or_404(
        QuizSession,
        code=code
    )

    data = {

        "current_question": session.current_question,

        "quiz_state": session.quiz_state,

        "timer_mode": session.timer_mode,

        "question_started_at": (
            session.question_started_at.timestamp()
            if session.question_started_at
            else None
        ),

        "question_time": session.default_time_per_question_seconds,

    }

    return JsonResponse(data)

from django.views.decorators.cache import never_cache

@never_cache
def session_status(request, code):
    session = get_object_or_404(QuizSession, code=code)
    return JsonResponse({"state": session.quiz_state})
    
def result_detail(request, code):
    session = get_object_or_404(QuizSession, code=code)
    participant = get_current_participant(request, session)

    if participant is None or not participant.submitted:
        messages.info(request, 'Attempt this quiz first to see your result.')
        return redirect('quizapp:session_room', code=session.code)

    leaderboard = session.participants.filter(submitted=True).order_by('-total_marks', 'submitted_at')
    responses = participant.responses.select_related('question', 'selected_choice')

    total_possible = session.total_possible_marks()

    if total_possible and total_possible > 0:
        percentage = round((participant.total_marks / total_possible) * 100, 2)
    else:
        percentage = 0

    total_participants = leaderboard.count()

    return render(request, 'quizapp/result_detail.html', {
        'session': session,
        'participant': participant,
        'leaderboard': leaderboard,
        'responses': responses,
        'total_possible': total_possible,
        'percentage': percentage,
        'total_participants': total_participants,
    })

# auto next question
@never_cache
@login_required
def check_question_timer(request, code):

    session = _get_hosted_session_or_404(request, code)

    # Only for per-question timer
    if (
        session.timer_mode != "per_question"
        or session.quiz_state != "running"
        or not session.question_started_at
    ):
        return JsonResponse({
            "changed": False,
            "finished": False,
        })

    questions = list(
        session.questions.order_by("order")
    )

    if not questions:
        return JsonResponse({
            "changed": False,
            "finished": False,
        })

    current_question = questions[session.current_question]

    question_time = (
        current_question.time_limit_seconds
        or session.default_time_per_question_seconds
    )

    elapsed = (
        timezone.now() - session.question_started_at
    ).total_seconds()

    # Time not over yet
    if elapsed < question_time:

        return JsonResponse({
            "changed": False,
            "finished": False,
        })

    # Move to next question
    if session.current_question < len(questions) - 1:

        session.current_question += 1
        session.question_started_at = timezone.now()

        session.save(update_fields=[
            "current_question",
            "question_started_at",
        ])

        return JsonResponse({
            "changed": True,
            "finished": False,
        })

    # Last question completed
    session.quiz_state = "finished"

    session.save(update_fields=[
        "quiz_state",
    ])

    return JsonResponse({
        "changed": False,
        "finished": True,
    })
    
# save answers for user
from django.views.decorators.http import require_POST
@require_POST
def save_answer(request, code):

    session = get_object_or_404(
        QuizSession,
        code=code
    )

    participant = get_current_participant(
        request,
        session
    )

    if participant is None:

        return JsonResponse(
            {"success": False},
            status=403
        )

    question = get_object_or_404(
        Question,
        id=request.POST.get("question_id"),
        session=session
    )

    choice = get_object_or_404(
        Choice,
        id=request.POST.get("choice_id"),
        question=question
    )

    marks = question.effective_marks()

    if choice.is_correct:
        is_correct = True
        marks_awarded = marks
    else:
        is_correct = False
        marks_awarded = -session.negative_marks if session.negative_marking else Decimal('0')

    Response.objects.update_or_create(

        participant=participant,
        question=question,

        defaults={

            "selected_choice": choice,
            "is_correct": is_correct,
            "marks_awarded": marks_awarded,

        }

    )

    return JsonResponse({

        "success": True

    })
    
def submit_quiz(request, code):

    session = get_object_or_404(QuizSession, code=code)
    participant = get_current_participant(request, session)

    if participant is None:
        messages.error(request, 'We could not find your participant record.')
        return redirect('quizapp:join_session')

    if not participant.submitted:

        questions = list(session.questions.all())
        responses = {
            r.question_id: r
            for r in participant.responses.select_related('selected_choice')
        }

        correct_count = 0
        wrong_count = 0
        not_attempted_count = 0
        total_marks = Decimal('0')

        for question in questions:
            response = responses.get(question.id)

            if response is None or response.selected_choice is None:
                not_attempted_count += 1
                continue

            if response.is_correct:
                correct_count += 1
            else:
                wrong_count += 1

            total_marks += response.marks_awarded

        participant.submitted = True
        participant.submitted_at = timezone.now()
        participant.total_marks = total_marks
        participant.correct_count = correct_count
        participant.wrong_count = wrong_count
        participant.not_attempted_count = not_attempted_count
        participant.save()

        session.recompute_ranks()

    return redirect(
        'quizapp:result_detail',
        code=session.code,
    )
    
# save result pdf
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet


@login_required
def download_results_pdf(request, code):

    session = get_object_or_404(
        QuizSession,
        code=code,
        host=request.user
    )

    participants = session.participants.filter(
        submitted=True
    ).order_by(
        "rank"
    )


    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{session.code}_results.pdf"'
    )


    doc = SimpleDocTemplate(response)


    styles = getSampleStyleSheet()

    content = []


    content.append(
        Paragraph(
            f"SunByte Quiz Result<br/>{session.title}",
            styles["Title"]
        )
    )

    content.append(Spacer(1,20))


    data = [
        [
            "Rank",
            "Participant",
            "Score"
        ]
    ]


    for p in participants:

        data.append(
            [
                p.rank,
                p.display_name,
                p.total_marks
            ]
        )


    table = Table(data)

    content.append(table)


    doc.build(content)


    return response


# delete account 
from django.contrib.auth import authenticate, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def delete_account(request):

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_delete = request.POST.get("confirm_delete")

        # Make sure checkbox is checked
        if not confirm_delete:
            messages.error(
                request,
                "Please confirm that you understand the account will be permanently deleted."
            )
            return redirect("delete_account")

        # Verify password directly against the logged-in user (safer than authenticate())
        if not request.user.check_password(password):
            messages.error(
                request,
                "Incorrect password. Account was not deleted."
            )
            return redirect("delete_account")

        # Store user before deleting
        user = request.user

        # Log out first
        logout(request)

        # Permanently delete account (cascades to related models automatically)
        user.delete()

        messages.success(
            request,
            "Your account has been permanently deleted."
        )

        return redirect("quizapp:home")

    return render(request, "quizapp/delete_account.html")


# category management
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Category
@login_required
@require_POST
def add_category(request):
    name = request.POST.get("name", "").strip()

    # Validate empty category
    if not name:
        return JsonResponse({
            "success": False,
            "error": "Category name is required."
        }, status=400)

    # Validate length
    if len(name) > 100:
        return JsonResponse({
            "success": False,
            "error": "Category name must be 100 characters or less."
        }, status=400)

    # Prevent duplicate categories ignoring letter case
    existing_category = Category.objects.filter(
        name__iexact=name
    ).first()

    if existing_category:
        return JsonResponse({
            "success": True,
            "id": existing_category.id,
            "name": existing_category.name,
            "existing": True
        })

    # Create new category
    category = Category.objects.create(
        name=name
    )

    return JsonResponse({
        "success": True,
        "id": category.id,
        "name": category.name,
        "existing": False
    })