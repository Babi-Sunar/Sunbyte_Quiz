from django.contrib import admin

from .models import Category, Choice, Participant, Question, QuizSession, Response


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('session', 'question_type', 'text', 'marks', 'time_limit_seconds', 'order')
    list_filter = ('question_type', 'session')
    search_fields = ('text',)
    inlines = [ChoiceInline]


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    fields = ('user', 'guest_name', 'submitted', 'total_marks', 'rank')
    readonly_fields = ('total_marks', 'rank')


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'host', 'category', 'status', 'question_count', 'player_count', 'created_at')
    list_filter = ('status', 'category', 'timer_mode', 'marks_mode')
    search_fields = ('title', 'code', 'host__username')
    inlines = [ParticipantInline]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'session', 'submitted', 'total_marks', 'correct_count', 'wrong_count', 'not_attempted_count', 'rank')
    list_filter = ('session', 'submitted')


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('participant', 'question', 'selected_choice', 'is_correct', 'marks_awarded')
    list_filter = ('is_correct',)
