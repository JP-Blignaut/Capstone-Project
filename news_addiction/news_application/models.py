from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User, AbstractUser
from django.db.models import Avg,Sum
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid
from django.conf import settings
from rest_framework import serializers
from django.core.mail import EmailMessage
# Create your models here.

class Roles(models.TextChoices):
    READER = 'READER', 'Reader'
    JOURNALIST = 'JOURNALIST', 'Journalist'
    EDITOR = 'EDITOR', 'Editor'

class ArticleStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'
    AWAITING_APPROVAL = 'AWAITING APPROVAL', 'Awaiting Editor Approval'
    REJECTED = 'REJECTED', 'Rejected by Editor'

class ArticleCategory(models.TextChoices):
    CURRENT_EVENTS = 'CURRENT_EVENTS', 'Current Events'
    SPORTS = 'SPORTS', 'Sports'
    PERSONAL_FINANCE = 'PERSONAL_FINANCE', 'Personal Finance'
    LIFESTYLE = 'LIFESTYLE', 'Lifestyle'
    CRIME = 'CRIME', 'Crime'
    POLITICS = 'POLITICS', 'Politics'
    ENTERTAINMENT = 'ENTERTAINMENT', 'Entertainment'
    OPINION = 'OPINION', 'Opinion'
    TECHNOLOGY = 'TECHNOLOGY', 'Technology' 


class User(AbstractUser):

    display_name = models.CharField(max_length=150)
    phone_number = PhoneNumberField(region="ZA")  # ZA = South Africa
    date_of_birth = models.DateField(blank=False, null=False)
    profile_picture = models.ImageField(upload_to="user_profile_pictures",
                                        blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.READER,
    )
    
    # Required fields for creating a superuser:
    REQUIRED_FIELDS = ['email', 'display_name', 'phone_number', 
                       'date_of_birth']

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
    
    def is_reader(self) -> bool:
        return self.role == Roles.READER

    def is_journalist(self) -> bool:
        return self.role == Roles.JOURNALIST

    def is_editor(self) -> bool:
        return self.role == Roles.EDITOR
    
# Each profile model has a one-to-one relationship with the User model.
# These models hold the extra fields unique to that role.
class ReaderProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, 
                                on_delete=models.CASCADE, 
                                related_name="reader_profile")
    
    def send_new_article_notification_email(self, article):
        """
        Send an email notification to the reader about a new
        article from a subscribed journalist or publisher.
        """
        subject = f"New Article Published on News Addiction!: {article.title}"
        user_email = self.user.email
        domain_email = "example@domain.com"
        body = (f"Hi {self.user.display_name},\n A new article has been "
                f" published from an entity you subscribe to.\n\n")
        body += f"Title: {article.title}\n"
        body += f"Author: {article.author.display_name}\n"
        body += f"Content: \n{article.content}\n\n"
        body += f"View the article and more at News Addiction!.co.za\n"
        email = EmailMessage(subject, body, domain_email, [user_email])
        email.send()


class JournalistProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name="journalist_profile")
    # Journalist-only fields:
    biography = models.TextField(blank=False)
    subscribers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="journalists_subscribed_to",
        blank=True,
        limit_choices_to={'role': Roles.READER}
    )
    
    
   

class EditorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, 
                                on_delete=models.CASCADE, 
                                related_name="editor_profile")
     # Editor-only fields:
    

class Publisher(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    website = models.URLField()
    email = models.EmailField()
    logo = models.ImageField(upload_to="publisher_logos", blank=True,
                             null=True)
    subscribers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="publishers_subscribed_to",
        blank=True,
        limit_choices_to={'role': Roles.READER}
    )

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="publishers_you_edit_for",
        blank=True,
        limit_choices_to={'role': Roles.EDITOR}
    )

    
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="publishers_you_write_for",
        blank=True,
        limit_choices_to={'role': Roles.JOURNALIST}
    )
    
                                         
    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    publication_date = models.DateTimeField(null=True, blank=True)
    publication_status = models.CharField(
        max_length=25,
        choices=ArticleStatus.choices,
        default=ArticleStatus.DRAFT,
        blank=True, null=False
    )
    
    image = models.ImageField(upload_to="article_images", blank=True,
                              null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="articles_authored",
        limit_choices_to={'role': Roles.JOURNALIST}
    )

    category = models.CharField(
        max_length=25,
        choices=ArticleCategory.choices,
        default=ArticleCategory.CURRENT_EVENTS,
    )
    

    # Generic Foreign Key for publisher (can be Publisher object if published
    # through a Publisher or a JournalistProfile object if self-published)
    publisher_content_type = models.ForeignKey(ContentType,
                                               on_delete=models.CASCADE, 
                                               null=True, 
                                               blank=True)
    publisher_object_id = models.PositiveIntegerField(null=True, blank=True)
    publisher = GenericForeignKey('publisher_content_type',
                                  'publisher_object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    @property
    def self_published(self):
        """ Return True if the article is self-published 
        (i.e., published by the journalist themselves)

        Returns:
            bool: True if self-published, False otherwise
        """
        if hasattr(self.publisher, 'name'):
            # It's a Publisher object
            return False
        elif hasattr(self.publisher, 'username'):
            # It's a User object (self-published)
            return True
        else:
            return "Not Published"

    def get_publisher_name(self):
        """
        Return the appropriate publisher name based on the publisher object
        type.
        """
        if not self.publisher:
            return "No Publisher"
        
        if not self.self_published:
            # It's a Publisher object
            return self.publisher.name
        else:
            # It's a User object (self-published)
            return self.publisher.display_name
    
        
    @property
    def published(self):
        """ Return True if the article is published"""
        return (self.publication_status == ArticleStatus.PUBLISHED)
    


    def __str__(self):
        return self.title


class ResetToken(models.Model):
    # Model to store password reset tokens for email-based password resets
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    token = models.CharField(max_length=500)
    expiry_date = models.DateTimeField()
    used = models.BooleanField(default=False)

class ArticleSerializer(serializers.ModelSerializer):

    author_display_name = serializers.CharField(source='author.display_name', 
                                                read_only=True)
    author_user_name = serializers.CharField(source='author.username', 
                                                read_only=True)
    publisher_name = serializers.SerializerMethodField()
    class Meta:
        model = Article
        fields = ['author_display_name', 'author_user_name',
                  'publisher_name'] + [f.name for f in Article._meta.fields]

    def get_publisher_name(self, obj):
        return obj.get_publisher_name()