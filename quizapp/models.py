import random
import string
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_session_code():
    """Generate a unique, human-friendly 6 character session code."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(alphabet, k=6))
        if not QuizSession.objects.filter(code=code).exists():
            return code


class Category(models.Model):
    """Program / stream a quiz belongs to, e.g. Engineering, IT, BCA,
    Medical, Entrance. Hosts can also add their own custom categories."""

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class QuizSession(models.Model):
    """A quiz session that a logged-in user hosts. Guests and logged-in
    users can join it using its code (or a QR code that encodes the same
    join link) without needing an account."""

    STATUS_CHOICES = (
        ('draft', 'Draft - building questions'),
        ('active', 'Live - open to join & attempt'),
        ('ended', 'Ended'),
    )
    QUIZ_STATE_CHOICES = (
    ('waiting', 'Waiting to Start'),
    ('running', 'Running'),
    ('paused', 'Paused'),
    ('finished', 'Finished'),
)
    TIMER_MODE_CHOICES = (
        ('none', 'No timer'),
        ('per_quiz', 'One timer for the whole quiz'),
        ('per_question', 'Separate timer for each question'),
    )
    MARKS_MODE_CHOICES = (
        ('uniform', 'Same marks for every question'),
        ('per_question', 'Custom marks per question'),
    )

    title = models.CharField(max_length=150)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions'
    )
    code = models.CharField(max_length=6, unique=True, default=generate_session_code, editable=False)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_sessions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    quiz_state = models.CharField(
    max_length=10,
    choices=QUIZ_STATE_CHOICES,
    default='waiting',
    )
    current_question = models.PositiveIntegerField(
    default=0
    )

    question_started_at = models.DateTimeField(
    null=True,
    blank=True
    )
    quiz_started_at = models.DateTimeField(
    null=True,
    blank=True
    )
    # ---- timer settings ----
    timer_mode = models.CharField(max_length=15, choices=TIMER_MODE_CHOICES, default='per_quiz')
    total_time_minutes = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    default=30,
    help_text='Used when timer mode is "whole quiz".'
    )
    default_time_per_question_seconds = models.PositiveIntegerField(
        default=60, help_text='Used when timer mode is "per question" and a question has no override.'
    )

    # ---- marking scheme ----
    marks_mode = models.CharField(max_length=15, choices=MARKS_MODE_CHOICES, default='uniform')
    default_marks = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    negative_marking = models.BooleanField(default=False)
    negative_marks = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text='Marks deducted for each wrong answer (enter as a positive number).'
    )

    shuffle_questions = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.code})'

    @property
    def player_count(self):
        return self.participants.count()

    @property
    def question_count(self):
        return self.questions.count()

    def total_possible_marks(self):
        if self.marks_mode == 'uniform':
            return self.default_marks * self.question_count
        return sum((q.marks or self.default_marks) for q in self.questions.all())

    def recompute_ranks(self):
        """Re-rank every participant who has submitted, best score first."""
        ranked = list(
            self.participants.filter(submitted=True).order_by('-total_marks', 'submitted_at')
        )
        for index, participant in enumerate(ranked, start=1):
            if participant.rank != index:
                participant.rank = index
                participant.save(update_fields=['rank'])


class Question(models.Model):
    TYPE_CHOICES = (
    ('mcq', 'Multiple Choice'),
    ('true_false', 'True / False'),
    )

    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='mcq')
    text = models.TextField()
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)
    video_file = models.FileField(upload_to='question_videos/', null=True, blank=True)
    video_url = models.URLField(blank=True, help_text='YouTube / external video link (optional).')

    marks = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Leave blank to use the session default (used only when marks mode is per-question).'
    )
    time_limit_seconds = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Leave blank to use the session default (used only when timer mode is per-question).'
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'Q{self.order}: {self.text[:50]}'

    def effective_marks(self):
        if self.session.marks_mode == 'per_question' and self.marks is not None:
            return self.marks
        return self.session.default_marks

    def effective_time_limit(self):
        if self.session.timer_mode != 'per_question':
            return None
        if self.time_limit_seconds:
            return self.time_limit_seconds
        return self.session.default_time_per_question_seconds


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='choice_images/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text or f'Choice {self.pk}'


class Participant(models.Model):
    """A user OR a guest (no account) who has joined a session."""

    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='joined_sessions'
    )
    guest_name = models.CharField(max_length=100, blank=True)
    guest_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    joined_at = models.DateTimeField(auto_now_add=True)
    submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)

    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    not_attempted_count = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-total_marks', 'submitted_at']

    def __str__(self):
        return f'{self.display_name} in {self.session.code}'

    @property
    def display_name(self):
        return self.user.username if self.user_id else (self.guest_name or 'Guest')

    @property
    def is_guest(self):
        return self.user_id is None


class Response(models.Model):
    """A participant's answer to a single question (or lack thereof)."""

    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('participant', 'question')

    def __str__(self):
        return f'{self.participant.display_name} -> {self.question_id}'
