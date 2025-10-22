from datetime import timedelta
import io
import json
import base64
from django.utils import timezone
from django.test import TestCase, Client
from .models import (Publisher, Article, ResetToken, User, Roles, 
                     ReaderProfile, JournalistProfile, EditorProfile,
                     ArticleCategory, ArticleStatus)
from datetime import date
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from .views import generate_reset_url, build_email_reset_password

# Create your tests here.


class UserFactory:
    """Factory class to create test users easily"""
    
    @staticmethod
    def create_reader(username="reader", email=None, password=None, **kwargs):
        if email is None:
            email = f"{username}@test.com"

        if password is None:
            password = "testpass123"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            display_name=kwargs.get("display_name", "Test Display Name"),
            phone_number=kwargs.get("phone_number", "+27725643208"),
            date_of_birth=kwargs.get("date_of_birth", date(1980, 1, 1)),
            role=Roles.READER
        )

        return user

    @staticmethod
    def create_journalist(username="journalist", email=None, password=None,
                          biography=None, **kwargs):
        if email is None:
            email = f"{username}@test.com"

        if password is None:
            password = "testpass123"

        if biography is None:
            biography = f"Biography for {username}"
            
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            display_name=kwargs.get("display_name", "Test Display Name"),
            phone_number=kwargs.get("phone_number", "+27725643209"),
            date_of_birth=kwargs.get("date_of_birth", date(1975, 1, 1)),
            role=Roles.JOURNALIST
        )
        user.journalist_profile.biography = biography
        return user
    
    @staticmethod
    def create_editor(username="editor", email=None, password=None, **kwargs):
        if email is None:
            email = f"{username}@test.com"

        if password is None:
            password = "testpass123"
            
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            display_name=kwargs.get("display_name", "Test Display Name"),
            phone_number=kwargs.get("phone_number", "+27555666777"),
            date_of_birth=kwargs.get("date_of_birth", date(1960, 1, 1)),
            role=Roles.EDITOR
        )

        return user
    
class PublisherFactory:
    """Factory class to create test publishers easily"""
    
    @staticmethod
    def create_publisher(name="Test Publisher", 
                         description="A Test publisher",
                         website="https://www.testpublisher.com",
                         email="test@publisher.com"):
        
        # Create a simple mock image file for testing
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        logo_file = SimpleUploadedFile(
            name='test_logo.jpg',
            content=temp_file.read(),
            content_type='image/jpeg'
        )
        
        return Publisher.objects.create(
            name=name,
            description=description,
            website=website,
            email=email,
            logo=logo_file
        )

    
class ArticleFactory:
    """Factory class to create test articles easily"""
    
    @staticmethod
    def create_article(title="Test Article",
                       content="Test Content",
                       author=None, publisher=None,
                       category=ArticleCategory.SPORTS,
                      **kwargs):
        if author is None:
            author = UserFactory.create_journalist()
        
        if publisher is None:
            publisher = PublisherFactory.create_publisher()
        
        # Create a simple mock image file for testing
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        logo_file = SimpleUploadedFile(
            name='test_logo.jpg',
            content=temp_file.read(),
            content_type='image/jpeg'
        )


        return Article.objects.create(
            title=title,
            content=content,
            author=author,
            publisher=publisher,
            category=category,
            image=logo_file,
        )

class TestUserModels(TestCase):
    """Test user model creation and relationships"""
    
    def test_create_reader(self):
        """Test creating a reader user with profile"""
        read_user = UserFactory.create_reader(username="test_reader")
        self.assertEqual(read_user.username, "test_reader")
        self.assertTrue(read_user.is_reader())
        self.assertFalse(read_user.is_journalist())
        self.assertFalse(read_user.is_editor())
        self.assertEqual(read_user.role, Roles.READER)
    
    def test_create_journalist(self):
        """Test creating a journalist user with profile"""
        journal_user = UserFactory.create_journalist(username="test_journalist")
        self.assertEqual(journal_user.username, "test_journalist")
        self.assertTrue(journal_user.is_journalist())
        self.assertFalse(journal_user.is_reader())
        self.assertFalse(journal_user.is_editor())
        self.assertEqual(journal_user.journalist_profile.biography, 
                         f"Biography for {journal_user.username}")
        self.assertEqual(journal_user.role, Roles.JOURNALIST)
    
    def test_create_editor(self):
        """Test creating an editor user with profile"""
        editor_user = UserFactory.create_editor(username="test_editor")
        self.assertEqual(editor_user.username, "test_editor")
        self.assertTrue(editor_user.is_editor())
        self.assertFalse(editor_user.is_reader())
        self.assertFalse(editor_user.is_journalist())
        self.assertEqual(editor_user.role, Roles.EDITOR)


    
class TestPublisherModel(TestCase):
    """Test publisher model creation and relationships"""
    
    def test_create_publisher(self):
        """Test creating a publisher"""
        publisher = PublisherFactory.create_publisher(name="My Publisher")
        self.assertEqual(publisher.name, "My Publisher")
        self.assertEqual(publisher.description, "A Test publisher")
        self.assertEqual(publisher.website, "https://www.testpublisher.com")
        self.assertEqual(publisher.email, "test@publisher.com")


class TestArticleModel(TestCase):
    """Test article model creation and relationships"""
    
    def test_create_article(self):
        """Test creating an article"""
        author = UserFactory.create_journalist(username="article_author")
        publisher = PublisherFactory.create_publisher(name="Article Publisher")
        article = ArticleFactory.create_article(
            title="My First Article",
            content="Test Content",
            author=author,
            publisher=publisher,
            category=ArticleCategory.SPORTS
        )
        self.assertEqual(article.title, "My First Article")
        self.assertEqual(article.content, "Test Content")
        self.assertEqual(article.author, author)
        self.assertEqual(article.publisher, publisher)
        self.assertEqual(article.category, ArticleCategory.SPORTS)
        self.assertIsNotNone(article.created_at)
        self.assertIsNotNone(article.updated_at)


class TestResetTokenModel(TestCase):
    def setUp(self):
        # Create a user object:
        self.read_user = UserFactory.create_reader(username="test_reader")

        # Create a ResetToken object
        self.reset_token = ResetToken.objects.create(
            user=self.read_user,
            token="test_token",
            expiry_date=timezone.now() + timedelta(hours=1),
            used=False
        )

    def test_reset_token_details(self):
        reset_token = ResetToken.objects.get(id=self.reset_token.id)
        self.assertEqual(reset_token.user.username, "test_reader")
        self.assertEqual(reset_token.token, "test_token")
        self.assertFalse(reset_token.used)
        self.assertTrue(reset_token.expiry_date > timezone.now())

class TestResetTokenExpiry(TestCase):
    def setUp(self):
        # Create a user object:
        self.read_user = UserFactory.create_reader(username="test_reader")

        # Create a ResetToken object
        self.reset_token = ResetToken.objects.create(
            user=self.read_user,
            token="test_token",
            expiry_date=timezone.now() - timedelta(hours=1),
            used=False
        )


    def test_reset_token_details(self):
        reset_token = ResetToken.objects.get(id=self.reset_token.id)
        self.assertEqual(reset_token.user.username, "test_reader")
        self.assertEqual(reset_token.token, "test_token")
        self.assertFalse(reset_token.used)
        self.assertTrue(reset_token.expiry_date < timezone.now())


class TestLoginView(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user object:
        self.read_user = UserFactory.create_reader(username="test_reader")
        self.journalist_user = UserFactory.create_journalist(
            username="test_journalist"
            )                                                      
        self.editor_user = UserFactory.create_editor(username="test_editor")


    def test_login_page_get_request(self):
        """Test that login page loads correctly with GET request"""
        response = self.client.get(reverse('login_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'form')

    def test_successful_reader_login(self):
        """Test successful login for reader user"""
        response = self.client.post(reverse('login_page'), {
            "username": self.read_user.username,
            "password": "testpass123"
        })

        # Check redirect to reader dashboard
        self.assertRedirects(response, reverse('reader_start_page'))
        
        # Verify user is logged in and session is set
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']),
                         self.read_user.id)
        self.assertEqual(self.client.session['user_id'], 
                         self.read_user.id)

    def test_successful_journalist_login(self):
        """Test successful login for journalist user"""
        response = self.client.post(reverse('login_page'), {
            "username": self.journalist_user.username,
            "password": "testpass123"
        })

        # Check redirect to journalist dashboard
        self.assertRedirects(response, reverse('journalist_start_page'))
        
        # Verify user is logged in and session is set
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']),
                         self.journalist_user.id)
        self.assertEqual(self.client.session['user_id'], 
                         self.journalist_user.id)
        
    def test_successful_editor_login(self):
        """Test successful login for editor user"""
        response = self.client.post(reverse('login_page'), {
            "username": self.editor_user.username,
            "password": "testpass123"
        })

        # Check redirect to editor dashboard
        self.assertRedirects(response, reverse('editor_start_page'))
        
        # Verify user is logged in and session is set
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']),
                         self.editor_user.id)
        self.assertEqual(self.client.session['user_id'], 
                         self.editor_user.id)
        
    def test_failed_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login_page'), {
            "username": self.read_user.username,
            "password": "wrongpassword"
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        
        # User should not be logged in
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_failed_login_nonexistent_user(self):
        """Test login with non-existent username"""
        response = self.client.post(reverse('login_page'), {
            'username': 'nonexistent_user',
            'password': 'anypassword'
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        
        # User should not be logged in
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_session_expiry_on_login(self):
        """Test that session expires on browser close"""
        response = self.client.post(reverse('login_page'), {
            "username": self.editor_user.username,
            "password": "testpass123"
        })
        
        # Follow the redirect to ensure session is fully processed
        self.assertRedirects(response, reverse('editor_start_page'))

        # Now check session expiry after the redirect is complete
        # The session should be set to expire at browser close
        session = self.client.session
        
        # Check if session is set to expire at browser close
        expire_at_browser_close = session.get_expire_at_browser_close()
        self.assertTrue(
            expire_at_browser_close,
            "Session should be set to expire when browser closes"
        )

    def test_empty_form_submission(self):
        """Test login with empty form"""
        response = self.client.post(reverse('login_page'), {})
        
        # Should stay on login page with form errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        
        # User should not be logged in
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_login_form_context(self):
        """Test that login form is properly passed to template"""
        response = self.client.get(reverse('login_page'))
        
        self.assertIn('form', response.context)
        self.assertIn('page_title', response.context)
        self.assertEqual(response.context['page_title'], 'Login')


class TestPasswordReset(TestCase):
    """Test cases for password reset functionality"""
    
    def setUp(self):
        """Set up test user and client"""
        self.user = UserFactory.create_reader(username="test_reader")
        self.client = Client()

    def test_reset_token_model_creation(self):
        """Test ResetToken model creation and properties"""
        from hashlib import sha1
        import secrets
        
        # Create a reset token manually
        token = str(secrets.token_urlsafe(16))
        hashed_token = sha1(token.encode()).hexdigest()
        expiry_date = timezone.now() + timedelta(minutes=5)
        
        reset_token = ResetToken.objects.create(
            user=self.user,
            token=hashed_token,
            expiry_date=expiry_date
        )
        
        # Test token properties
        self.assertEqual(reset_token.user, self.user)
        self.assertEqual(reset_token.token, hashed_token)
        self.assertFalse(reset_token.used)
        self.assertEqual(reset_token.expiry_date, expiry_date)
    
    def test_request_reset_password_view_get(self):
        """Test GET request to password reset request page"""
        response = self.client.get(reverse('request_reset_password_page'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Request Password Reset')
        self.assertIn('form', response.context)
        
    def test_request_reset_password_valid_user(self):
        """Test password reset request with valid user credentials"""
        # Ensure no reset tokens exist initially
        self.assertEqual(ResetToken.objects.count(), 0)
        
        response = self.client.post(reverse('request_reset_password_page'), {
            'username': self.user.username,
            'email': self.user.email
        })
        
        # Should redirect to login page
        self.assertRedirects(response, reverse('login_page'))
        
        # A reset token should be created
        self.assertEqual(ResetToken.objects.count(), 1)
        
        # Check that token is associated with correct user
        token = ResetToken.objects.first()
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.used)
        
        # Check that expiry date is set to future (5 minutes)
        self.assertGreater(token.expiry_date, timezone.now())
        
    def test_request_reset_password_invalid_user(self):
        """Test password reset request with non-existent user"""
        response = self.client.post(reverse('request_reset_password_page'), {
            'username': 'nonexistent',
            'email': 'nonexistent@example.com'
        })
        
        # Should redirect to login page
        self.assertRedirects(response, reverse('login_page'))
        
        # No reset token should be created
        self.assertEqual(ResetToken.objects.count(), 0)
        
    def test_request_reset_password_mismatched_credentials(self):
        """Test password reset request with mismatched username and email"""
        response = self.client.post(reverse('request_reset_password_page'), {
            'username': self.user.username,
            'email': 'wrong@example.com'
        })
        
        # Should redirect to login page
        self.assertRedirects(response, reverse('login_page'))
        
        # No reset token should be created
        self.assertEqual(ResetToken.objects.count(), 0)
        

        
    def test_reset_password_with_valid_token(self):
        """Test password reset with valid token"""
        from hashlib import sha1
        import secrets
        
        # Create a reset token
        token = str(secrets.token_urlsafe(16))
        hashed_token = sha1(token.encode()).hexdigest()
        expiry_date = timezone.now() + timedelta(minutes=5)
        
        reset_token = ResetToken.objects.create(
            user=self.user,
            token=hashed_token,
            expiry_date=expiry_date
        )
        
        # GET request to reset password page
        response = self.client.get(reverse('password_reset', args=[token]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset Password')
        
        # POST request to actually reset password
        response = self.client.post(reverse('password_reset', args=[token]), {
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })
        
        # Should redirect to login page
        self.assertRedirects(response, reverse('login_page'))
        
        # Token should be deleted after use
        self.assertEqual(ResetToken.objects.count(), 0)
        
        # User password should be changed
        updated_user = User.objects.get(id=self.user.id)
        self.assertTrue(updated_user.check_password('newpassword123'))
        self.assertFalse(updated_user.check_password('testpass123'))
        
    def test_reset_password_with_expired_token(self):
        """Test password reset with expired token"""
        from hashlib import sha1
        import secrets
        
        # Create an expired reset token
        token = str(secrets.token_urlsafe(16))
        hashed_token = sha1(token.encode()).hexdigest()
        expiry_date = timezone.now() - timedelta(minutes=1)  # Expired
        
        reset_token = ResetToken.objects.create(
            user=self.user,
            token=hashed_token,
            expiry_date=expiry_date
        )
        
        # Try to access reset password page with expired token
        response = self.client.get(reverse('password_reset', args=[token]))
        
        # Should redirect to request reset password page
        self.assertRedirects(response, reverse('request_reset_password_page'))
        
        # Expired token should be deleted
        self.assertEqual(ResetToken.objects.count(), 0)
        
    def test_reset_password_with_invalid_token(self):
        """Test password reset with invalid/non-existent token"""
        fake_token = "invalid_token_123"
        
        response = self.client.get(reverse('password_reset', args=[fake_token]))
        
        # Should redirect to request reset password page
        self.assertRedirects(response, reverse('request_reset_password_page'))
        
    def test_reset_password_form_validation(self):
        """Test password reset form validation"""
        from hashlib import sha1
        import secrets
        
        # Create a valid reset token
        token = str(secrets.token_urlsafe(16))
        hashed_token = sha1(token.encode()).hexdigest()
        expiry_date = timezone.now() + timedelta(minutes=5)
        
        reset_token = ResetToken.objects.create(
            user=self.user,
            token=hashed_token,
            expiry_date=expiry_date
        )
        
        # Test with mismatched passwords
        response = self.client.post(reverse('password_reset', args=[token]), {
            'new_password1': 'newpassword123',
            'new_password2': 'differentpassword'
        })
        
        # Should stay on reset password page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        
        # Token should still exist
        self.assertEqual(ResetToken.objects.count(), 1)
        
        # User password should not be changed
        updated_user = User.objects.get(id=self.user.id)
        self.assertTrue(updated_user.check_password('testpass123'))
        
    def test_generate_reset_url_function(self):
        """Test the generate_reset_url function"""
        
        
        # Generate reset URL
        reset_url = generate_reset_url(self.user)
        
        # Check that URL is properly formatted
        self.assertTrue(reset_url.startswith(
            "http://127.0.0.1:8000/reset_password/"))
        
        # Check that a reset token was created
        self.assertEqual(ResetToken.objects.count(), 1)
        
        token = ResetToken.objects.first()
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.used)
        
    def test_build_email_reset_password_function(self):
        """Test the build_email_reset_password function"""
        
        reset_url = "http://127.0.0.1:8000/reset_password/test_token"
        email = build_email_reset_password(self.user, reset_url)
        
        # Check email properties
        self.assertEqual(email.subject, "Password Reset Requested")
        self.assertEqual(email.to, [self.user.email])
        self.assertIn(self.user.username, email.body)
        self.assertIn(reset_url, email.body)


class TestJournalistViews(TestCase):
    """Test journalist-specific views and functionality"""
    
    def setUp(self):
        """Set up test data for journalist view tests"""
        self.client = Client()
        self.journalist = UserFactory.create_journalist(
            username="test_journalist",
            email="journalist@test.com",
            password="testpass123"
        )
        self.publisher = PublisherFactory.create_publisher()
        
        # Assign journalist to publisher (required for article creation)
        self.journalist.publishers_you_write_for.add(self.publisher)
        self.journalist.save()
        
    def test_journalist_can_add_article_via_view(self):
        """Test that a journalist can successfully add an article via view"""
        
        # Log in as journalist
        login_successful = self.client.login(
            username="test_journalist",
            password="testpass123"
        )
        self.assertTrue(login_successful)
        
        # Prepare article data
        article_data = {
            'title': 'Test Article Title',
            'content': 'This is the content of the test article.',
            'category': ArticleCategory.CURRENT_EVENTS,
        }
        
        # Count articles before submission
        initial_article_count = Article.objects.count()
        
        # Submit POST request to add article
        response = self.client.post(
            reverse('journalist_article_add_page'),
            data=article_data,
            follow=True
        )
        
        # Check that article was created
        self.assertEqual(Article.objects.count(), initial_article_count + 1)
        
        # Get the created article
        created_article = Article.objects.latest('id')
        
        # Verify article properties
        self.assertEqual(created_article.title, article_data['title'])
        self.assertEqual(created_article.content, article_data['content'])
        self.assertEqual(created_article.category, article_data['category'])
        self.assertEqual(created_article.author, self.journalist)
        
        # Check that response redirects to article management page
        self.assertRedirects(
            response,
            reverse('journalist_article_management_page')
        )
        
        # Verify article is in DRAFT status by default
        self.assertEqual(
            created_article.publication_status,
            ArticleStatus.DRAFT
        )
        
    def test_journalist_add_article_view_requires_authentication(self):
        """Test that the add article view requires authentication"""
        
        # Try to access add article view without logging in
        response = self.client.get(reverse('journalist_article_add_page'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        
    def test_journalist_add_article_view_get_request(self):
        """Test GET request to add article view returns form"""
        
        # Log in as journalist
        self.client.login(username="test_journalist", password="testpass123")
        
        # GET request to add article view
        response = self.client.get(reverse('journalist_article_add_page'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertContains(response, 'title')
        self.assertContains(response, 'content')
        self.assertContains(response, 'category')
        
    def test_journalist_add_article_with_invalid_data(self):
        """Test that invalid article data is handled properly"""
        
        # Log in as journalist
        self.client.login(username="test_journalist", password="testpass123")
        
        # Submit empty form data
        response = self.client.post(
            reverse('journalist_article_add_page'),
            data={}
        )
        
        # Should return form with errors (not redirect)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        
        # No article should be created
        self.assertEqual(Article.objects.count(), 0)


class TestEditorViews(TestCase):
    """Test editor-specific views and functionality"""
    
    def setUp(self):
        """Set up test data for editor view tests"""
        self.client = Client()
        
        # Create users
        self.editor = UserFactory.create_editor(
            username="test_editor",
            email="editor@test.com",
            password="testpass123"
        )
        self.journalist = UserFactory.create_journalist(
            username="test_journalist",
            email="journalist@test.com",
            password="testpass123"
        )
        self.another_journalist = UserFactory.create_journalist(
            username="another_journalist",
            email="another_journalist@test.com",
            password="testpass123"
        )
        
        # Create publisher and assign editor
        self.publisher = PublisherFactory.create_publisher(
            name="Test Publisher for Editor"
        )
        self.publisher.editors.add(self.editor)
        self.publisher.save()
        
        # Create an article by journalist for testing approval
        self.test_article = ArticleFactory.create_article(
            title="Test Article for Approval",
            content="This article needs editor approval",
            author=self.journalist,
            category=ArticleCategory.CURRENT_EVENTS
        )
        
    def test_editor_can_assign_journalist_to_publisher(self):
        """Test that an editor can assign a journalist to a publisher"""
        
        # Log in as editor
        login_successful = self.client.login(
            username="test_editor",
            password="testpass123"
        )
        self.assertTrue(login_successful)
        
        # Verify journalist is not initially assigned to publisher
        self.assertNotIn(
            self.journalist,
            self.publisher.journalists.all()
        )
        
        # Prepare assignment data
        assignment_data = {
            'journalist_choice': str(self.journalist.id)
        }
        
        # Submit POST request to assign journalist
        response = self.client.post(
            reverse('editor_journalist_assign_page', args=[self.publisher.pk]),
            data=assignment_data,
            follow=True
        )
        
        # Refresh publisher from database
        self.publisher.refresh_from_db()
        
        # Check that journalist was assigned to publisher
        self.assertIn(self.journalist, self.publisher.journalists.all())
        
        # Check that response redirects to journalist management page
        self.assertRedirects(
            response,
            reverse('editor_journalist_management_page',
                    args=[self.publisher.pk])
        )
        
    def test_editor_can_approve_article_publication_status(self):
        """Test that an editor can approve/change article publication status"""
        
        # Log in as editor
        self.client.login(username="test_editor", password="testpass123")
        
        # Assign article to the publisher via content type
        publisher_content_type = ContentType.objects.get_for_model(Publisher)
        self.test_article.publisher_content_type = publisher_content_type
        self.test_article.publisher_object_id = self.publisher.pk
        self.test_article.publication_status = ArticleStatus.DRAFT
        self.test_article.save()
        
        # Verify article is initially in DRAFT status
        self.assertEqual(
            self.test_article.publication_status,
            ArticleStatus.DRAFT
        )
        
        # Prepare data to approve article (publish it)
        approval_data = {
            'title': self.test_article.title,
            'content': self.test_article.content,
            'category': self.test_article.category,
            'publication_status': ArticleStatus.PUBLISHED,
        }
        
        # Submit POST request to edit/approve article
        response = self.client.post(
            reverse('editor_article_edit_page', args=[self.test_article.pk]),
            data=approval_data,
            follow=True
        )
        
        # Refresh article from database
        self.test_article.refresh_from_db()
        
        # Check that article status was changed to PUBLISHED
        self.assertEqual(
            self.test_article.publication_status,
            ArticleStatus.PUBLISHED
        )
        
        # Check that response redirects to article detail page
        self.assertRedirects(
            response,
            reverse('editor_article_detail_page', args=[self.test_article.pk])
        )
        
    def test_editor_assign_journalist_view_requires_authentication(self):
        """Test that assign journalist view requires authentication"""
        
        # Try to access assign journalist view without logging in
        response = self.client.get(
            reverse('editor_journalist_assign_page', args=[self.publisher.pk])
        )
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        
    def test_editor_assign_journalist_view_get_request(self):
        """Test GET request to assign journalist view returns form"""
        
        # Log in as editor
        self.client.login(username="test_editor", password="testpass123")
        
        # GET request to assign journalist view
        response = self.client.get(
            reverse('editor_journalist_assign_page', args=[self.publisher.pk])
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertContains(response, 'journalist_choice')
        self.assertIn('publisher', response.context)
        self.assertEqual(response.context['publisher'], self.publisher)
        
    def test_editor_can_only_assign_to_their_publishers(self):
        """Test that editor can only assign journalists to their publishers"""
        
        # Create another publisher not assigned to this editor
        other_publisher = PublisherFactory.create_publisher(
            name="Other Publisher"
        )
        
        # Log in as editor
        self.client.login(username="test_editor", password="testpass123")
        
        # Try to access assign journalist view for other publisher
        response = self.client.get(
            reverse('editor_journalist_assign_page', args=[other_publisher.pk])
        )
        
        # Should return 404 (not found) since editor not assigned
        self.assertEqual(response.status_code, 404)
        
    def test_editor_assign_multiple_journalists(self):
        """Test that an editor can assign multiple journalists to publisher"""
        
        # Log in as editor
        self.client.login(username="test_editor", password="testpass123")
        
        # Assign first journalist
        self.client.post(
            reverse('editor_journalist_assign_page', args=[self.publisher.pk]),
            data={'journalist_choice': str(self.journalist.id)}
        )
        
        # Assign second journalist
        self.client.post(
            reverse('editor_journalist_assign_page', args=[self.publisher.pk]),
            data={'journalist_choice': str(self.another_journalist.id)}
        )
        
        # Refresh publisher from database
        self.publisher.refresh_from_db()
        
        # Check that both journalists are assigned
        assigned_journalists = self.publisher.journalists.all()
        self.assertIn(self.journalist, assigned_journalists)
        self.assertIn(self.another_journalist, assigned_journalists)
        self.assertEqual(assigned_journalists.count(), 2)
        
    def test_editor_article_management_view_shows_publisher_articles(self):
        """Test that editor article management shows only publisher articles"""
        
        # Log in as editor
        self.client.login(username="test_editor", password="testpass123")
        
        # Assign article to publisher
        publisher_content_type = ContentType.objects.get_for_model(Publisher)
        self.test_article.publisher_content_type = publisher_content_type
        self.test_article.publisher_object_id = self.publisher.pk
        self.test_article.save()
        
        # Create another article not assigned to this publisher
        other_article = ArticleFactory.create_article(
            title="Other Article",
            author=self.another_journalist
        )
        
        # GET request to article management view
        response = self.client.get(
            reverse('editor_article_management_page', args=[self.publisher.pk])
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_article.title)
        self.assertNotContains(response, other_article.title)
        self.assertIn('articles', response.context)
        self.assertIn('publisher', response.context)
        self.assertEqual(response.context['publisher'], self.publisher)
        
    def test_editor_can_reject_article(self):
        """Test that an editor can reject an article"""
        
        # Log in as editor
        self.client.login(username="test_editor", password="testpass123")
        
        # Assign article to publisher
        publisher_content_type = ContentType.objects.get_for_model(Publisher)
        self.test_article.publisher_content_type = publisher_content_type
        self.test_article.publisher_object_id = self.publisher.pk
        self.test_article.publication_status = ArticleStatus.AWAITING_APPROVAL
        self.test_article.save()
        
        # Prepare data to reject article
        rejection_data = {
            'title': self.test_article.title,
            'content': self.test_article.content,
            'category': self.test_article.category,
            'publication_status': ArticleStatus.REJECTED,
        }
        
        # Submit POST request to edit/reject article
        self.client.post(
            reverse('editor_article_edit_page', args=[self.test_article.pk]),
            data=rejection_data,
            follow=True
        )
        
        # Refresh article from database
        self.test_article.refresh_from_db()
        
        # Check that article status was changed to REJECTED
        self.assertEqual(
            self.test_article.publication_status,
            ArticleStatus.REJECTED
        )


class TestReaderViews(TestCase):
    """Test all reader-related views and functionality"""
    
    def setUp(self):
        """Set up test data for reader view tests"""
        # Create test users
        self.reader = UserFactory.create_reader(
            username="test_reader",
            email="reader@test.com"
        )
        self.journalist = UserFactory.create_journalist(
            username="test_journalist",
            email="journalist@test.com"
        )
        self.editor = UserFactory.create_editor(
            username="test_editor",
            email="editor@test.com"
        )
        
        # Create test publisher
        self.publisher = PublisherFactory.create_publisher(
            name="Test News Publisher"
        )
        
        # Create test articles
        self.article1 = ArticleFactory.create_article(
            title="Test Article 1",
            content="Content for test article 1",
            author=self.journalist,
            publisher=self.publisher
        )
        
        self.article2 = ArticleFactory.create_article(
            title="Breaking News",
            content="Content for breaking news",
            author=self.journalist,
            publisher=self.publisher
        )
        
        # Create self-published article
        self.self_published_article = ArticleFactory.create_article(
            title="Self Published Article",
            content="Content for self published article",
            author=self.journalist,
            publisher=self.journalist
        )
        self.self_published_article.publication_status = (
            ArticleStatus.PUBLISHED
        )
        self.self_published_article.save()
        
        self.client = Client()
    
    def test_reader_start_view_authenticated(self):
        """Test that authenticated readers can access the start view"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # GET request to reader start view
        response = self.client.get(reverse('reader_start_page'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search articles by title...")
        self.assertContains(response, "Welcome to News Addiction! - "
                            "All the Latest News at Your Fingertips"
                    )
        self.assertIn('articles', response.context)
        self.assertEqual(len(response.context['articles']), 3)  # All articles
    
    def test_reader_start_view_unauthenticated(self):
        """Test that unauthenticated users cannot access reader start view"""
        response = self.client.get(reverse('reader_start_page'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_reader_start_view_search_functionality(self):
        """Test search functionality in reader start view"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # Search for "Breaking"
        response = self.client.get(
            reverse('reader_start_page'),
            {'search': 'Breaking'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to News Addiction!")
        self.assertNotContains(response, "Test Article 1")
        self.assertEqual(len(response.context['articles']), 1)
        self.assertEqual(response.context['search_query'], 'Breaking')
    
    def test_reader_start_view_empty_search(self):
        """Test search with empty query returns all articles"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # Search with empty string
        response = self.client.get(
            reverse('reader_start_page'),
            {'search': ''}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['articles']), 3)  # All articles
        self.assertEqual(response.context['search_query'], '')
    
    def test_reader_view_article(self):
        """Test that readers can view individual articles"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # GET request to view specific article
        response = self.client.get(
            reverse('reader_view_article_page', args=[self.article1.id])
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article1.title)
        self.assertContains(response, self.article1.content)
        self.assertEqual(response.context['article'], self.article1)
        self.assertEqual(response.context['page_title'], self.article1.title)
    
    def test_reader_view_journalist_details(self):
        """Test that readers can view journalist details"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # GET request to view journalist details
        response = self.client.get(
            reverse('reader_view_journalist_details_page', 
                   args=[self.journalist.id, self.article1.id])
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.journalist.display_name)
        self.assertEqual(response.context['journalist'], self.journalist)
        self.assertEqual(response.context['previous_article_id'], 
                         self.article1.id)
        # Not subscribed initially:
        self.assertFalse(response.context['reader_subscribed'])
    
    def test_reader_view_journalist_details_when_subscribed(self):
        """Test journalist details view when reader is subscribed"""
        # Subscribe reader to journalist
        self.journalist.journalist_profile.subscribers.add(self.reader)
        
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # GET request to view journalist details
        response = self.client.get(
            reverse('reader_view_journalist_details_page', 
                   args=[self.journalist.id, self.article1.id])
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['reader_subscribed'])
    
    def test_reader_view_publisher_details_regular_article(self):
        """Test that readers can view publisher details for regular articles"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # Set up content type for publisher
        publisher_content_type = ContentType.objects.get_for_model(Publisher)
        self.article1.publisher_content_type = publisher_content_type
        self.article1.publisher_object_id = self.publisher.id
        self.article1.save()
        
        # GET request to view publisher details
        response = self.client.get(
            reverse('reader_view_publisher_details_page', 
                   args=[self.article1.id])
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.publisher.name)
        self.assertEqual(response.context['publisher'], self.publisher)
        self.assertEqual(response.context['article'], self.article1)
        # Not subscribed initially:
        self.assertFalse(response.context['reader_subscribed'])  
    
    def test_reader_view_publisher_details_self_published_redirects(self):
        """Test that self-published articles redirect to journalist details"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # GET request to view publisher details for self-published article
        response = self.client.get(
            reverse('reader_view_publisher_details_page', 
                   args=[self.self_published_article.id])
        )
        
        # Should redirect to journalist details
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('reader_view_journalist_details_page',
                             args=[self.journalist.id,
                                   self.self_published_article.id])
        self.assertRedirects(response, expected_url)
    
    def test_reader_journalist_subscribe(self):
        """Test that readers can subscribe to journalists"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # Ensure reader is not subscribed initially
        self.assertFalse(
            self.journalist.journalist_profile.subscribers.filter(
                id=self.reader.id
            ).exists()
        )
        
        # POST request to subscribe
        response = self.client.post(
            reverse('reader_journalist_subscribe_unsubscribe_page',
                   args=[self.journalist.id, self.article1.id])
        )
        
        # Should redirect back to journalist details
        expected_url = reverse('reader_view_journalist_details_page',
                             args=[self.journalist.id, self.article1.id])
        self.assertRedirects(response, expected_url)
        
        # Check that reader is now subscribed
        self.assertTrue(
            self.journalist.journalist_profile.subscribers.filter(
                id=self.reader.id
            ).exists()
        )
    
    def test_reader_journalist_unsubscribe(self):
        """Test that readers can unsubscribe from journalists"""
        # Subscribe reader to journalist first
        self.journalist.journalist_profile.subscribers.add(self.reader)
        
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # Ensure reader is subscribed initially
        self.assertTrue(
            self.journalist.journalist_profile.subscribers.filter(
                id=self.reader.id
            ).exists()
        )
        
        # POST request to unsubscribe
        response = self.client.post(
            reverse('reader_journalist_subscribe_unsubscribe_page',
                   args=[self.journalist.id, self.article1.id])
        )
        
        # Should redirect back to journalist details
        expected_url = reverse('reader_view_journalist_details_page',
                             args=[self.journalist.id, self.article1.id])
        self.assertRedirects(response, expected_url)
        
        # Check that reader is no longer subscribed
        self.assertFalse(
            self.journalist.journalist_profile.subscribers.filter(
                id=self.reader.id
            ).exists()
        )
    
    def test_reader_publisher_subscribe(self):
        """Test that readers can subscribe to publishers"""
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # Ensure reader is not subscribed initially
        self.assertFalse(
            self.publisher.subscribers.filter(id=self.reader.id).exists()
        )
        
        # POST request to subscribe
        response = self.client.post(
            reverse('reader_publisher_subscribe_unsubscribe_page',
                   args=[self.publisher.id, self.article1.id])
        )
        
        # Should redirect back to publisher details
        expected_url = reverse('reader_view_publisher_details_page',
                             args=[self.article1.id])
        self.assertRedirects(response, expected_url)
        
        # Check that reader is now subscribed
        self.assertTrue(
            self.publisher.subscribers.filter(id=self.reader.id).exists()
        )
    
    def test_reader_publisher_unsubscribe(self):
        """Test that readers can unsubscribe from publishers"""
        # Subscribe reader to publisher first
        self.publisher.subscribers.add(self.reader)
        
        # Log in as reader
        self.client.login(username="test_reader", password="testpass123")
        
        # Ensure reader is subscribed initially
        self.assertTrue(
            self.publisher.subscribers.filter(id=self.reader.id).exists()
        )
        
        # POST request to unsubscribe
        response = self.client.post(
            reverse('reader_publisher_subscribe_unsubscribe_page',
                   args=[self.publisher.id, self.article1.id])
        )
        
        # Should redirect back to publisher details
        expected_url = reverse('reader_view_publisher_details_page',
                             args=[self.article1.id])
        self.assertRedirects(response, expected_url)
        
        # Check that reader is no longer subscribed
        self.assertFalse(
            self.publisher.subscribers.filter(id=self.reader.id).exists()
        )
    
    def test_non_reader_cannot_access_reader_views(self):
        """Test that non-readers cannot access reader-specific views"""
        # Log in as journalist (not a reader)
        self.client.login(username="test_journalist", password="testpass123")
        
        # Try to access reader start view
        response = self.client.get(reverse('reader_start_page'))
        
        # Should redirect (user_passes_test decorator)
        self.assertEqual(response.status_code, 302)
        
        # Try to access reader article view
        response = self.client.get(
            reverse('reader_view_article_page', args=[self.article1.id])
        )
        
        # Should redirect
        self.assertEqual(response.status_code, 302)


class APIGetArticlesTestCase(TestCase):
    """Test cases for the API_get_articles view"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.journalist1 = UserFactory.create_journalist(
            username="test_journalist_1",
            email="journalist1@test.com"
        )
        self.journalist2 = UserFactory.create_journalist(
            username="test_journalist_2", 
            email="journalist2@test.com"
        )
        
        # Create test publishers
        self.publisher1 = PublisherFactory.create_publisher(
            name="Test Publisher 1",
            description="First test publisher"
        )
        self.publisher2 = PublisherFactory.create_publisher(
            name="Test Publisher 2", 
            description="Second test publisher"
        )
        
        # Create test articles
        self.article1 = Article.objects.create(
            title="Article by Journalist 1",
            content="Content of article by journalist 1",
            author=self.journalist1,
            publisher=self.publisher1,
            category=ArticleCategory.POLITICS,
            publication_status=ArticleStatus.PUBLISHED
        )
        
        self.article2 = Article.objects.create(
            title="Another Article by Journalist 1", 
            content="More content by journalist 1",
            author=self.journalist1,
            publisher=self.publisher2,
            category=ArticleCategory.SPORTS,
            publication_status=ArticleStatus.PUBLISHED
        )
        
        self.article3 = Article.objects.create(
            title="Article by Journalist 2",
            content="Content by journalist 2",
            author=self.journalist2,
            publisher=self.publisher1,
            category=ArticleCategory.TECHNOLOGY,
            publication_status=ArticleStatus.PUBLISHED
        )
        
        # Create a test user for API authentication
        self.api_user = self.journalist1
        
        self.client = Client()
        
    def test_api_get_articles_with_specific_author(self):
        """Test API request to get articles by a specific author"""
        # Authenticate the request
        credentials = base64.b64encode(b'test_journalist_1:testpass123').decode('ascii')
        # Make API request with specific author name
        response = self.client.get(
            '/get/articles/',
            {'author_name': 'test_journalist_1'},
            HTTP_AUTHORIZATION=f'Basic {credentials}'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Should return 2 articles by test_journalist_1
        self.assertEqual(len(response_data), 2)
        
        # Check that all returned articles are by the correct author
        for article_data in response_data:
            self.assertEqual(article_data['author_user_name'], 'test_journalist_1')
            
        # Check specific article titles are included
        article_titles = [article['title'] for article in response_data]
        self.assertIn("Article by Journalist 1", article_titles)
        self.assertIn("Another Article by Journalist 1", article_titles)
        
    def test_api_get_articles_with_nonexistent_author(self):
        """Test API request with an author that doesn't exist"""
        credentials = base64.b64encode(b'test_journalist_1:testpass123').decode('ascii')
        
        response = self.client.get(
            '/get/articles/',
            {'author_name': 'nonexistent_author'},
            HTTP_AUTHORIZATION=f'Basic {credentials}'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Should return empty list
        self.assertEqual(len(response_data), 0)
        
    def test_api_get_articles_without_authentication(self):
        """Test API request without authentication should fail"""
        response = self.client.get(
            '/get/articles/',
            {'author_name': 'test_journalist_1'}
        )
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
        
    def test_api_get_articles_all_articles(self):
        """Test API request to get all articles (no filter)"""
        credentials = base64.b64encode(b'test_journalist_1:testpass123').decode('ascii')
        
        response = self.client.get(
            '/get/articles/',
            HTTP_AUTHORIZATION=f'Basic {credentials}'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Should return all 3 articles
        self.assertEqual(len(response_data), 3)
        
    def test_api_get_articles_with_publisher_filter(self):
        """Test API request to get articles by publisher"""
        credentials = base64.b64encode(b'test_journalist_1:testpass123').decode('ascii')
        
        response = self.client.get(
            '/get/articles/',
            {'publisher_name': 'Test Publisher 1'},
            HTTP_AUTHORIZATION=f'Basic {credentials}'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Should return 2 articles from Test Publisher 1
        self.assertEqual(len(response_data), 2)
        
        # Check that all returned articles are from the correct publisher
        for article_data in response_data:
            self.assertEqual(article_data['publisher_name'], 'Test Publisher 1')
            
    def test_api_get_articles_with_both_author_and_publisher_filter(self):
        """Test API request with both author and publisher filters"""
        credentials = base64.b64encode(b'test_journalist_1:testpass123').decode('ascii')
        
        response = self.client.get(
            '/get/articles/',
            {
                'author_name': 'test_journalist_1',
                'publisher_name': 'Test Publisher 1'
            },
            HTTP_AUTHORIZATION=f'Basic {credentials}'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Should return 1 article (journalist 1 + publisher 1)
        self.assertEqual(len(response_data), 1)
        
        article_data = response_data[0]
        self.assertEqual(article_data['author_user_name'], 'test_journalist_1')
        self.assertEqual(article_data['publisher_name'], 'Test Publisher 1')
        self.assertEqual(article_data['title'], 'Article by Journalist 1')

