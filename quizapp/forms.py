from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import Category, Choice, Participant, Question, QuizSession


class SignUpForm(UserCreationForm):
    """Matches the Sign Up screen: Username, Email, Password, Confirm Password."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'E-mail', 'class': 'form-input'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Username', 'class': 'form-input'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password', 'class': 'form-input'})
        self.fields['password1'].label = 'Password'
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password', 'class': 'form-input'})
        self.fields['password2'].label = 'Confirm Password'
        for field in self.fields.values():
            field.help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    """Matches the Login screen: Email, Password, Remember Me."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'E-mail here...', 'class': 'form-input'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password here...', 'class': 'form-input'})
    )
    remember_me = forms.BooleanField(required=False, label='Remember Me')


# ---------------------------------------------------------------------
# Joining a session — works for guests (no account) and logged-in users.
# A guest only ever has to type a display name + the session code
# (or scan a QR code that pre-fills the code).
# ---------------------------------------------------------------------
class JoinSessionForm(forms.Form):
    display_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your name', 'class': 'form-input'}),
    )
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter session code',
            'class': 'form-input code-input',
        }),
    )

    def __init__(self, *args, user_is_authenticated=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_is_authenticated = user_is_authenticated
        if user_is_authenticated:
            self.fields['display_name'].widget = forms.HiddenInput()
        else:
            self.fields['display_name'].required = True

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()


# ---------------------------------------------------------------------
# Session builder (host only)
# ---------------------------------------------------------------------
class SessionSettingsForm(forms.ModelForm):
    new_category = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Or type a new program name', 'class': 'form-input'}),
        label='Add a new program (optional)',
    )

    class Meta:
        model = QuizSession
        fields = (
            'title', 'category',
            'timer_mode', 'total_time_minutes', 'default_time_per_question_seconds',
            'marks_mode', 'default_marks',
            'negative_marking', 'negative_marks',
            'shuffle_questions',
        )
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Engineering Entrance Mock Test 1', 'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'timer_mode': forms.Select(attrs={'class': 'form-input'}),
            'total_time_minutes': forms.NumberInput(attrs={
            'class': 'form-input',
            'min': 1,
            'step': 1
            }),
            'default_time_per_question_seconds': forms.NumberInput(attrs={'class': 'form-input', 'min': 5}),
            'marks_mode': forms.Select(attrs={'class': 'form-input'}),
            'default_marks': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5', 'min': 0}),
            'negative_marks': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.25', 'min': 0}),
        }
        labels = {
            'negative_marking': 'Enable negative marking',
            'negative_marks': 'Marks deducted per wrong answer',
            'shuffle_questions': 'Shuffle question order for each participant',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].empty_label = 'Select a program'

    def clean(self):
        cleaned = super().clean()
        new_category_name = cleaned.get('new_category')
        if new_category_name:
            category, _ = Category.objects.get_or_create(
                name=new_category_name.strip(),
                defaults={'description': 'Added by a host while creating a session.'},
            )
            cleaned['category'] = category
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('category'):
            instance.category = self.cleaned_data['category']
        if commit:
            instance.save()
        return instance


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question

        fields = (
            'question_type',
            'text',
            'image',
            'video_file',
            'video_url',
            'marks',
            'time_limit_seconds'
        )

        widgets = {
            'question_type': forms.Select(
                attrs={
                    'class': 'form-input',
                    'id': 'id_question_type'
                }
            ),

            'text': forms.Textarea(
                attrs={
                    'class': 'form-input',
                    'rows': 3,
                    'placeholder': 'Question text'
                }
            ),

            'video_file': forms.FileInput(
                attrs={
                    'class': 'form-input',
                    'accept': 'video/*'
                }
            ),

            'video_url': forms.URLInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'https://youtube.com/... (optional)'
                }
            ),

            'marks': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'step': '0.5',
                    'placeholder': 'Uses session default if left blank'
                }
            ),

            'time_limit_seconds': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Uses session default if left blank'
                }
            ),
        }

# Up to 6 choices per question (covers "four option" and general MCQ).
# True/False questions are auto-generated in the view, not through this formset.
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=("text", "image", "is_correct"),
    extra=4,
    max_num=4,
    min_num=4,
    validate_min=True,
    validate_max=True,
    can_delete=False,
    widgets={
        "text": forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Option text",
            }
        ),
    },
)

class TrueFalseAnswerForm(forms.Form):
    correct_answer = forms.ChoiceField(
        choices=(('true', 'True'), ('false', 'False')),
        widget=forms.RadioSelect,
        label='Correct answer',
    )
