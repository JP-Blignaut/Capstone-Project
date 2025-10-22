from urllib import request
import os
from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.auth import login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import (AuthenticationForm, UserCreationForm, 
                                       PasswordResetForm, SetPasswordForm
                                       )
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMessage
from django.contrib import messages
from django.db.models import Prefetch
import secrets
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from hashlib import sha1
from .models import (ArticleStatus, Roles, User, ReaderProfile, 
                     JournalistProfile, EditorProfile,
                     Publisher, Article, ResetToken, ArticleSerializer
                     )
from .forms import (CustomUserCreationForm, CustomPasswordResetForm, 
                    ArticleForm, ArticlePublishForm, EditorArticleForm, 
                    AssignJournalistsToPublisherForm
                    )
 

from django.http import JsonResponse
from rest_framework.decorators import (api_view, renderer_classes,
                                       authentication_classes,
                                       permission_classes
                                       )
from rest_framework_xml.renderers import XMLRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from .functions.tweet import Tweet

# Create your views here.

def in_group_editor(user):
    return user.groups.filter(name="Editors").exists()

def in_group_reader(user):
    return user.groups.filter(name="Readers").exists()

def in_group_journalist(user):
    return user.groups.filter(name="Journalists").exists()

def login_view(request):
    """
    Login view using Django"s AuthenticationForm.
    """
  
        
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session["user_id"] = user.id
            request.session.set_expiry(0)  # Session expires on browser close
    
    
            user_groups = user.groups.all()
            # Redirect to the appropriate dashboard based on user group:
            if user_groups.filter(name="Readers").exists():
                return redirect("reader_start_page")
            elif user_groups.filter(name="Editors").exists():
                return redirect("editor_start_page")
            elif user_groups.filter(name="Journalists").exists():
                return redirect("journalist_start_page")

    else:
        form = AuthenticationForm(request)

    return render(request, "news_application/login.html", 
                  {"form": form, "page_title": "Login"})


def register_new_user_view(request):
    """
    Simple registration view using Django"s built-in UserCreationForm.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # log the user in immediately after registration
            login(request, user)

            
            # Add the user to the group selected during registratio

            user_groups = user.groups.all()
            if user_groups.filter(name="Readers").exists():
                return redirect("reader_start_page")
            elif user_groups.filter(name="Editors").exists():
                return redirect("editor_start_page")
            elif user_groups.filter(name="Journalists").exists():
                return redirect("journalist_start_page")
        
    else:
        form = CustomUserCreationForm()

    return render(request, "news_application/register_new_user.html",
                  {"form": form, "page_title": "Register"})

def logout_view(request):
    """
    Simple logout view that logs out the user and redirects to login page.
    """
    logout(request)
    return redirect("login_page")

def request_reset_password_view(request):
    """
    Simple view to handle password reset requests.
    """
    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            # Generate reset URL, send email - if the user exists and 
            # email matches:

            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(username__iexact=username,
                                        email__iexact=email,
                                        is_active=True
                                        )
                reset_url = generate_reset_url(user)
                email = build_email_reset_password(user, reset_url)
                email.send()

                # Show message that email has been sent at login page:
                messages.success(
                    request,
                    "Password reset email sent! Please check your inbox."
                )
                # Redirect to login page:
                return redirect("login_page")
            
            except User.DoesNotExist:
                # Show error if user details are invalid:
                messages.error(
                    request, (
                        "No active user found with the "
                        "provided username and email!"
                    )
                )
                # Redirect to login page:
                return redirect("login_page")
    else:
        form = CustomPasswordResetForm()

    return render(request, "news_application/request_reset_password.html",
                  {"form": form,"page_title": "Request Password Reset"})


def generate_reset_url(user):
    """
    Generate a password reset URL for the given user.
    This function creates a unique token and constructs a URL that can be
    sent to the user"s email for password reset.

    Args:
        user (User): The user requesting the password reset.
    Returns:
        str: The complete password reset URL.
    """
    domain = "http://127.0.0.1:8000/"
    url = f"{domain}reset_password/"
    token = str(secrets.token_urlsafe(16))
    expiry_date = timezone.now() + timedelta(minutes=5)
    reset_token = ResetToken.objects.create(
        user=user,
        token=sha1(token.encode()).hexdigest(),
        expiry_date=expiry_date
    )
    url += f"{token}"
    return url


def build_email_reset_password(user, reset_url):
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


def reset_user_password_view(request, token):
    """
    View to handle password reset using a token.
    """
    # Validate the token
    try:
        hashed_token = sha1(token.encode()).hexdigest()
        user_token = ResetToken.objects.get(token=hashed_token)
        
        # Check if token has expired
        if user_token.expiry_date < timezone.now():
            user_token.delete()
            messages.error(
                request,
                "This password reset link has expired. "
                "Please request a new one."
            )
            return redirect("request_reset_password_page")
            
    except ResetToken.DoesNotExist:
        messages.error(
            request,
            "Invalid password reset link. "
            "Please request a new one."
        )
        return redirect("request_reset_password_page")
    
    # Get the user associated with this token
    user = user_token.user
    
    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            # Save the new password
            form.save()
            
            # Delete the used token to prevent reuse
            user_token.delete()
            
            # Show success message and redirect to login
            messages.success(
                request,
                "Your password has been reset successfully. "
                "You can now log in with your new password."
            )
            return redirect("login_page")
    else:
        form = SetPasswordForm(user)
    
    return render(request, "news_application/reset_password.html", {
        "form": form,
        "token": token,
        "user": user
    })

@user_passes_test(in_group_reader)
def reader_start_view(request):
    """
    View to display reader start page - allowing Readers to browse articles
    and newsletters.
    """
    # Get search query from GET parameters
    search_query = request.GET.get("search", "").strip()

    # Start with all articles
    articles = Article.objects.all()
    
    # Filter by search query if provided
    if search_query:
        articles = articles.filter(
            title__icontains=search_query
        )

    return render(request, "news_application/reader_start.html",
                  {"page_title": "Welcome!",
                   "articles": articles,
                   "search_query": search_query})

@user_passes_test(in_group_reader)
def reader_view_article(request, article_id):
    """
    View to display a single article to the reader.
    """
    article = get_object_or_404(Article, pk=article_id)
    return render(request, "news_application/reader_view_article.html",
                  {"page_title": article.title,
                   "article": article})

@user_passes_test(in_group_reader)
def reader_view_journalist_details(request, journalist_id, article_id):
    """
    View to display details of a specific journalist to the reader.
    """
    journalist = get_object_or_404(User, pk=journalist_id,
                                   role=Roles.JOURNALIST)
    
    if journalist.journalist_profile.subscribers.filter(
        id=request.user.id).exists():
        reader_subscribed = True
    else:
        reader_subscribed = False

    return render(request, 
                  "news_application/reader_view_journalist_details.html",
                  {"page_title": (f"Journalist Profile - ",
                                  f"{journalist.display_name}"),
                   "reader_subscribed": reader_subscribed,
                   "journalist": journalist,
                   "previous_article_id": article_id}
    )

@user_passes_test(in_group_reader)
def reader_view_publisher_details(request, article_id):
    """
    View to display details of a specific publisher to the reader.
    """

    article = get_object_or_404(Article, pk=article_id)
    if article.self_published:
        # Return to journalist details if self-published:
        return redirect("reader_view_journalist_details_page",
                        journalist_id=article.author.id,
                        article_id=article.id
                        )
    else:
        # Return to publisher details if not self-published:
        publisher = get_object_or_404(Publisher, pk=article.publisher.id)

        publisher_content_type = ContentType.objects.get_for_model(Publisher)
        articles_published = Article.objects.filter(
            publisher_content_type=publisher_content_type,
            publisher_object_id=article.publisher.id
            ).count()

        if publisher.subscribers.filter(
            id=request.user.id).exists():
            reader_subscribed = True
        else:
            reader_subscribed = False

        return render(request,
                    "news_application/reader_view_publisher_details.html",
                    {"page_title": (f"Publisher Profile - ",
                                    f"{publisher.name}"),
                    "reader_subscribed": reader_subscribed,
                    "publisher": publisher,
                    "articles_published": articles_published,
                    "article": article
                    }
                    )

@user_passes_test(in_group_reader)
def reader_journalist_subscribe_unsubscribe(request, journalist_id,
                                            article_id):
    """
    View to allow a reader to subscribe or unsubscribe from a journalist.
    """
    journalist = get_object_or_404(User, pk=journalist_id,
                                   role=Roles.JOURNALIST)
    
    if journalist.journalist_profile.subscribers.filter(
        id=request.user.id).exists():
        # Unsubscribe the reader
        journalist.journalist_profile.subscribers.remove(request.user)
        messages.success(request, 
                         f"You have unsubscribed from "
                         f"{journalist.display_name}.")
    else:
        # Subscribe the reader
        journalist.journalist_profile.subscribers.add(request.user)
        messages.success(request, 
                         f"You have subscribed to {journalist.display_name}.")
    
    return redirect("reader_view_journalist_details_page", 
                    journalist_id=journalist.id, article_id=article_id)


@user_passes_test(in_group_reader)
def reader_publisher_subscribe_unsubscribe(request, publisher_id, article_id):
    """
    View to allow a reader to subscribe or unsubscribe from a publisher.
    """
    publisher = get_object_or_404(Publisher, pk=publisher_id)
    
    if publisher.subscribers.filter(
        id=request.user.id).exists():
        # Unsubscribe the reader
        publisher.subscribers.remove(request.user)
        messages.success(request, 
                         f"You have unsubscribed from "
                         f"{publisher.name}.")
    else:
        # Subscribe the reader
        publisher.subscribers.add(request.user)
        messages.success(request, 
                         f"You have subscribed to {publisher.name}.")

    return redirect("reader_view_publisher_details_page", 
                    article_id=article_id)

@user_passes_test(in_group_journalist)
def journalist_start_view(request):
    """
    View to display journalist start page - allowing Journalists to manage their articles
    and newsletters.
    """
    return render(request, "news_application/journalist_start.html",
                  {"page_title": "Journalist Dashboard"})

@user_passes_test(in_group_editor)
def editor_start_view(request):
    """
    View to display editor start page - allowing Editors to manage their articles
    and newsletters.
    """
    assigned_publishers = Publisher.objects.filter(editors=request.user)
    

    return render(request, "news_application/editor_start.html",
                  {"page_title": "Editor Dashboard",
                   "assigned_publishers": assigned_publishers})

@user_passes_test(in_group_journalist)
def journalist_article_management_view(request):
    """
    View to display journalist article management page - allowing Journalists to
    manage their articles.
    """
    articles = Article.objects.filter(author=request.user)
    return render(
        request, 
        "news_application/journalist_article_management.html",
        {"page_title": "Article Management", "articles": articles,
         "ArticleStatus": ArticleStatus}
        )

@user_passes_test(in_group_journalist)
def journalist_article_add_view(request):
    """
    View to create a new article.
    :param request: HTTP request object.
    :return: Rendered template for creating a new article.
    """
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            return redirect("journalist_article_management_page")
    else:
        form = ArticleForm()
    return render(request, "news_application/journalist_article_form.html", 
                  {"form": form})

@user_passes_test(in_group_journalist)
def journalist_article_edit_view(request, pk):
    """
    View to update an existing article.

    :param request: HTTP request object.
    :param pk: Primary key of the article to be updated.
    :return: Rendered template for updating the specified article.
    """
    article = get_object_or_404(Article, pk=pk, author=request.user)
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save(commit=False)
            article.save()
            return redirect("journalist_article_detail_page", pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, "news_application/journalist_article_form.html", 
                  {"form": form, "article": article})

@user_passes_test(in_group_journalist)
def journalist_article_detail_view(request, pk):
    """
    View to display the details of a specific article.

    :param request: HTTP request object.
    :param pk: Primary key of the product to be displayed.
    :return: Rendered template showing the details of the specified product.
    """
    article = get_object_or_404(Article, pk=pk, author=request.user)
    return render(request, "news_application/journalist_article_detail.html", 
                  {"article": article})

@user_passes_test(in_group_journalist)
def journalist_article_delete_view(request, pk):
    """
    View to delete an existing article.

    :param request: HTTP request object.
    :param pk: Primary key of the article to be deleted.
    :return: Redirects to the article management page after publishing.
    """
    article = get_object_or_404(Article, pk=pk, author=request.user)
    if request.method == "POST":
        article.delete()
        return redirect("journalist_article_management_page")
    return render(request, 
                  "news_application/journalist_article_confirm_delete.html", 
                  {"article": article}
                  )

@user_passes_test(in_group_journalist)
def journalist_article_publish_view(request, pk):
    """
    View to publish an existing article.

    :param request: HTTP request object.
    :param pk: Primary key of the article to be published.
    :return: Rendered template for publishing the specified article.
    """
    article = get_object_or_404(Article, pk=pk, author=request.user)
    if request.method == "POST":
        form = ArticlePublishForm(request.POST, request.FILES, 
                                  instance=article, user=request.user)
        if form.is_valid():
            article = form.save(commit=False)
            article.save()
            return redirect("journalist_article_management_page")
    else:
        form = ArticlePublishForm(instance=article, user=request.user)
    return render(request,
                  "news_application/journalist_article_publish_form.html", 
                  {"form": form, "article": article}
                  )


@user_passes_test(in_group_editor)
def editor_publisher_dashboard_view(request, pk):
    """
    View to display editor publisher dashboard page - allowing Editors to 
    manage their assigned publisher.
    """
    publisher = get_object_or_404(Publisher, pk=pk, editors=request.user)
    
    return render(request, "news_application/editor_publisher_dashboard.html",
                  {"page_title": f"Editor Dashboard - {publisher.name}",
                   "publisher": publisher})


@user_passes_test(in_group_editor)
def editor_journalist_management_view(request, pk):
    """
    View to display editor journalist management page - allowing Editors to 
    manage journalists assigned to their publisher.
    """
    publisher = get_object_or_404(Publisher, pk=pk, editors=request.user)
    journalists = publisher.journalists.all()
    
    return render(request, "news_application/editor_journalist_management.html",
                  {"page_title": f"Journalist Management - {publisher.name}",
                   "publisher": publisher,
                   "journalists": journalists})

@user_passes_test(in_group_editor)
def editor_assign_journalist_view(request, pk):
    """
    View to assign a journalist to a publisher.
    """
    publisher = get_object_or_404(Publisher, pk=pk, editors=request.user)
    
    if request.method == "POST":
        form = AssignJournalistsToPublisherForm(
            request.POST, 
            instance=publisher,
            user=request.user
        )
        if form.is_valid():
            publisher = form.save(commit=False)
            publisher.save()
            return redirect("editor_journalist_management_page", pk=publisher.pk)
    else:
        form = AssignJournalistsToPublisherForm(instance=publisher, 
                                                user=request.user)
    
    return render(request, "news_application/editor_assign_journalist_form.html", 
                  {"form": form, "publisher": publisher})


@user_passes_test(in_group_editor)
def editor_journalist_remove_assignment_view(request, publisher_pk, 
                                             journalist_pk):
    """
    View to remove a specific journalist from a publisher with confirmation.

    :param request: HTTP request object.
    :param publisher_pk: Primary key of the publisher.
    :param journalist_pk: Primary key of the journalist to be removed.
    :return: Rendered confirmation template (GET) or redirect after removal 
    (POST).
    """
    publisher = get_object_or_404(Publisher, pk=publisher_pk, 
                                  editors=request.user)
    journalist = get_object_or_404(User, pk=journalist_pk)

    if request.method == "POST":
        # User confirmed removal
        publisher.journalists.remove(journalist)
        messages.success(request, (f"Journalist '{journalist.username}' " 
                         f" has been unassigned from the publisher."))
        return redirect("editor_journalist_management_page", pk=publisher.pk)

    # Show confirmation page
    return render(
        request, 
        "news_application/editor_journalist_remove_assignment_confirm.html", 
        {"publisher": publisher, "journalist": journalist})


@user_passes_test(in_group_editor)
def editor_article_management_view(request, pk):
    """
    View to display editor article management page - allowing Editors to
    manage articles for their assigned publisher.
    """
    
    
    publisher = get_object_or_404(Publisher, pk=pk, editors=request.user)
    publisher_content_type = ContentType.objects.get_for_model(Publisher)
    articles = Article.objects.filter(
        publisher_content_type=publisher_content_type,
        publisher_object_id=publisher.pk).select_related("author"
        )
      
    
    return render(
        request,
        "news_application/editor_article_management.html",
        {
            "page_title": f"Article Management - {publisher.name}", 
            "publisher": publisher,
            "articles": articles,
            "user": request.user,
            "ArticleStatus": ArticleStatus
        }
    )

@user_passes_test(in_group_editor)
def editor_article_detail_view(request, pk):
    """
    View to display the details of a specific article.

    :param request: HTTP request object.
    :param pk: Primary key of the product to be displayed.
    :return: Rendered template showing the details of the specified product.
    """
    article = get_object_or_404(Article, pk=pk)
    return render(request, "news_application/editor_article_detail.html", 
                  {"article": article})

@user_passes_test(in_group_editor)
def editor_article_edit_view(request, pk):
    """
    View to update an existing article.

    :param request: HTTP request object.
    :param pk: Primary key of the article to be updated.
    :return: Rendered template for updating the specified article.
    """
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        form = EditorArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save(commit=False)
            article.save()
            return redirect("editor_article_detail_page", pk=article.pk)
    else:
        form = EditorArticleForm(instance=article)
    return render(request, "news_application/editor_article_form.html", 
                  {"form": form, "article": article})

@user_passes_test(in_group_editor)
def editor_article_delete_view(request, pk):
    """
    View to delete an existing article.

    :param request: HTTP request object.
    :param pk: Primary key of the article to be deleted.
    :return: Redirects to the article management page after publishing.
    """
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        article.delete()
        return redirect("editor_article_management_page")
    return render(request, 
                  "news_application/editor_article_confirm_delete.html", 
                  {"article": article}
                  )

@user_passes_test(in_group_editor)
def editor_reject_for_publication_view(request, pk):
    """
    View to reject an existing article for publication.
    Directly rejects the article and redirects without intermediate page.

    :param request: HTTP request object.
    :param pk: Primary key of the article to be rejected.
    :return: Redirects to the article management page after rejecting.
    """
    article = get_object_or_404(Article, pk=pk)
    article.publication_status = ArticleStatus.REJECTED
    article.save()
    messages.success(request, f"Article '{article.title}' "
                     f"has been rejected for publication.\n"
                     f"The author will be notified via email."
                     )
    return redirect("editor_article_management_page", pk=article.publisher.pk)

@user_passes_test(in_group_editor)
def editor_accept_for_publication_view(request, pk):
    """
    View to reject an existing article for publication.
    Directly rejects the article and redirects without intermediate page.

    :param request: HTTP request object.
    :param pk: Primary key of the article to be rejected.
    :return: Redirects to the article management page after rejecting.
    """
    article = get_object_or_404(Article, pk=pk)
    article.publication_status = ArticleStatus.PUBLISHED
    article.publication_date = timezone.now()
    article.save()
    messages.success(request, f"Article '{article.title}' "
                     f"has been accepted for publication.\n"
                     f"All subscribers will be notified via email."
                     )
    return redirect("editor_article_management_page", pk=article.publisher.pk)








def publisher_name_q(publisher_name: str) :
    """
    Build a Q() that matches Article.publisher (GenericForeignKey) to either:
      - Publisher objects whose .name matches publisher_name, OR
      - User objects (self-published) whose username matches publisher_name
    """

    # Figure out content types for both possible targets
    ct_publisher = ContentType.objects.get_for_model(Publisher)
    ct_user = ContentType.objects.get_for_model(User)

    # IDs that match the provided name on each concrete model
    publisher_ids = Publisher.objects.filter(
        name__iexact=publisher_name
    ).values_list("id", flat=True)

    user_ids = User.objects.filter(
        Q(username__iexact=publisher_name)
    ).values_list("id", flat=True)

    # Build the OR across the two content types
    return (
        Q(publisher_content_type=ct_publisher,
          publisher_object_id__in=publisher_ids)
        |
        Q(publisher_content_type=ct_user,
          publisher_object_id__in=user_ids)
    )



@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def API_get_articles(request):
    """API Request to View all articles, or if the request contains the keyword
    'author_name' then filter by that author, if request contains the keyword
    'publisher_name' then filter by that publisher.

    Args:
        request (HttpRequest): The HTTP request object.
    """
    if request.method == "GET":
        author_name = request.GET.get('author_name')
        publisher_name = request.GET.get('publisher_name')

        query_articles = Article.objects.all().select_related("author")

        if author_name:
            query_articles = query_articles.filter(
                author__username__iexact=author_name)
        
        
        # Generic ForeignKey filtering (publisher can be Publisher or User):
        if publisher_name:
            query_articles = query_articles.filter(
                publisher_name_q(publisher_name))

        serializer = ArticleSerializer(query_articles, many=True)
        return JsonResponse(serializer.data, safe=False)
    