from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from .models import (User, Roles, ReaderProfile, JournalistProfile, 
                     EditorProfile, Article, ArticleStatus)
from .functions.tweet import Tweet



# Ensure that every time a User instance is created, the appropriate profile
# instance is also created, and the user is added to the correct group.
# This signal handler listens for the post_save signal from the User model.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Create the appropriate profile based on the user's role
    if instance.role == Roles.READER:
        group, _ = Group.objects.get_or_create(name="Readers")
        instance.groups.add(group)
        ReaderProfile.objects.create(user=instance)
        # Grant custom permission here later, example:
        # perm = Permission.objects.get(codename="add_article")
        # instance.user_permissions.add(perm)

    elif instance.role == Roles.JOURNALIST:
        
        group, _ = Group.objects.get_or_create(
            name="Journalists"
            )
        JournalistProfile.objects.create(
            user=instance, 
            biography="Default biography - Please update."
        )
    
        instance.groups.add(group)
        
    elif instance.role == Roles.EDITOR:
        EditorProfile.objects.create(user=instance)
        group, _ = Group.objects.get_or_create(name="Editors")
        instance.groups.add(group)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.role == Roles.READER and hasattr(instance, 'reader_profile'):
        instance.reader_profile.save()
    elif (instance.role == Roles.JOURNALIST and
           hasattr(instance, 'journalist_profile')):
        instance.journalist_profile.save()
    elif instance.role == Roles.EDITOR and hasattr(instance, 'editor_profile'):
        instance.editor_profile.save()


@receiver(post_save, sender=Article)
def notify_subscribers(sender, instance, **kwargs):
    if not (instance.publication_status == ArticleStatus.PUBLISHED):
        return  # Only notify on published articles

    # Always notify subscribers of the author when an article is published:
    subscribers = (
        instance.author.journalist_profile.subscribers.all()
    )

    if not instance.self_published:
        # If Published through a Publisher, also get publisher's subscribers
        subscribers_publisher = instance.publisher.subscribers.all()
        subscribers = subscribers | subscribers_publisher
    # Send an email notification to each subscriber:
    for subscriber in subscribers.distinct():
        subscriber.reader_profile.send_new_article_notification_email(instance)

    # Post the article on the sites Twitter account:
    tweet_text = f"New Article Published on News Addiction!:\n"
    tweet_text += f"Title: {instance.title}\n"
    tweet_text += f"Author: {instance.author.display_name}\n"
    tweet_text += f"Content: \n{instance.content}\n\n"
    tweet_text += f"View the article and more at News Addiction!.co.za"
    
    if instance.image:
        image_path = instance.image.path
    else:
        image_path = None
    # Skip tweeting during tests - user input required:
    if getattr(settings, 'TESTING', False):
        return  
    Tweet._instance.make_tweet(tweet_text, image_path)