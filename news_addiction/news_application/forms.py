from django import forms
from django.core.mail import EmailMessage
from .models import (Article, User, ReaderProfile, JournalistProfile, 
                     EditorProfile, Roles, ArticleCategory, Publisher,
                     ArticleStatus)
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import  Group
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import copy

class CustomUserCreationForm(UserCreationForm):
    # A Custom user creation form that includes an email address and 
    # group selection.


    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Roles.choices, required=True, 
                              label="Role")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "role",
                  "display_name", "phone_number", "date_of_birth",
                  "profile_picture")
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"})
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
    

class CustomPasswordResetForm(PasswordResetForm):
    # A custom password reset form that uses both username and 
    # email to identify the user.
    username = forms.CharField(label="Username", max_length=150)
    email = forms.EmailField(label="Email", max_length=254)
    
    # Specify field order to ensure username appears first
    field_order = ["username", "email"] 

    def get_users(self, email):
        # Override get_users to filter by both email and username
        username = self.cleaned_data.get("username")
        email = self.cleaned_data.get("email")
        active_users = User._default_manager.filter(
            email__iexact=email,
            username__iexact=username,
            is_active=True
        )
        return (u for u in active_users if u.has_usable_password())
    
    def build_email(user, reset_url):
        """Builds a password reset email.

        Args:
            user (User): The user requesting the password reset.
            reset_url (str): The URL to reset the password.

        Returns:
            EmailMessage: The constructed email message.
        """
        subject = "Password Reset Requested"
        user_email = user.email
        domain_email = "example@domain.com"
        body = f"Hi {user.username},\nHere is your link to reset your "
        body += f"password: {reset_url}"
        email = EmailMessage(subject, body, domain_email, [user_email])
        return email
    
class ArticleForm(forms.ModelForm):
    category = forms.ChoiceField(choices=ArticleCategory.choices, 
                                 required=True, 
                                label="Category"
                                )
    class Meta:
        
        model = Article
        fields = ["title", "content", "category", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", 
                                             "rows": 20}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"})
        }

class EditorArticleForm(forms.ModelForm):
    """Editor Article Form that allows the editor to also adjust the 
       publication status, effectively removing an article from publication.
    """
    category = forms.ChoiceField(choices=ArticleCategory.choices, 
                                 required=True, 
                                label="Category"
                                )
    
    # Define published field with explicit choices for better UX
    publication_status = forms.ChoiceField(
        choices=ArticleStatus.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Publication Status",
        required=True
    )

    
    class Meta:
        model = Article
        fields = ["title", "content", "category", "image", 
                  "publication_status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", 
                                             "rows": 20}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"})
        }


class ArticlePublishForm(forms.ModelForm):
    """
    Form for journalists to publish articles with publisher selection.
    Allows selection from assigned publishers or self-publishing option.
    Only allows modification of publisher and publication date.
    """
    PUBLISH_DIRECTLY = "DIRECT"
    DEFAULT_CHOICES = [(PUBLISH_DIRECTLY, "Publish Directly (Self-Published)")]
    # Build choices for publisher selection
    publisher_choice = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        required=True,
        label="Publication Option",
        widget=forms.RadioSelect,
        help_text=("Choose how you want to publish this article\nOnce "
        "published, an article will be available to all readers.")
    )
    
    class Meta:
        model = Article
        fields = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_journalist():
            # Get the publishers assigned to the journalist:
            assigned_publishers = user.publishers_you_write_for.all()
            
            # Create a LOCAL copy of choices for this instance
            choices = copy.deepcopy(self.DEFAULT_CHOICES)

            for publisher in assigned_publishers:
                choices.append((str(publisher.id), 
                                f"Publish through {publisher.name}"))
            
            self.fields["publisher_choice"].choices = choices
            
            # If no assigned publishers, only show direct publishing option
            if not assigned_publishers.exists():
                self.fields["publisher_choice"].help_text = (
                    "You are not assigned to any publishers. "
                    "Your article will be self-published."
                )
                    
    def save(self, commit=True):
        article = super().save(commit=False)
        
        # Handle publisher assignment based on selection
        publisher_choice = self.cleaned_data.get("publisher_choice")
        
        if publisher_choice == self.PUBLISH_DIRECTLY:
            # Set publisher to the journalist"s profile for self-publishing
        
            content_type = ContentType.objects.get_for_model(article.author)
            article.publisher_content_type = content_type
            article.publisher_object_id = article.author.id
            # Only publish automatically if published directly:
            if publisher_choice == self.PUBLISH_DIRECTLY:
                article.publication_status = ArticleStatus.PUBLISHED
                article.publication_date = timezone.now()
        else:
            # Set publisher to the selected Publisher
            publisher_id = int(publisher_choice)
            publisher = Publisher.objects.get(id=publisher_id)
            article.publisher_content_type = ContentType.objects.get_for_model(
                Publisher)
            article.publisher_object_id = publisher.id
            # If publishing through a publisher, set status to pending:
            article.publication_status = ArticleStatus.AWAITING_APPROVAL  

        
        
        if commit:
            article.save()
        
        return article
    


class AssignJournalistsToPublisherForm(forms.ModelForm):
    """
    Form for assigning journalists to a publisher.
    """

    # Build choices for journalist selection
    journalist_choice = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        required=True,
        label="Assign Journalist to Publisher",
        widget=forms.Select,
        help_text="Choose a journalist to assign to this publisher"
    )
    
    class Meta:
        model = Publisher
        fields = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and user.is_editor():
            # Get all registered journalists:
            journalists = User.objects.filter(role=Roles.JOURNALIST).exclude(
                publishers_you_write_for=self.instance
            )
            choices = []
            for journalist in journalists:
                choices.append((str(journalist.id),f"{journalist.username}"))
            
            self.fields["journalist_choice"].choices = choices

            # If no assigned journalists, only show direct publishing option
            if not journalists.exists():
                self.fields["journalist_choice"].help_text = (
                    "No Journalists are registered on the platform. "
                    "You cannot assign any journalists at this time."
                )
                    
    def save(self, commit=True):
        publisher = super().save(commit=False)
        
        # Handle publisher assignment based on selection
        journalist_choice = self.cleaned_data.get("journalist_choice")

        # Assign the selected journalist to the Publisher
        journalist_id = int(journalist_choice)
        journalist = User.objects.get(id=journalist_id)
        publisher.journalists.add(journalist)

        if commit:
            publisher.save()
        
        return publisher