import json
from io import BytesIO
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.http import JsonResponse
from unittest.mock import patch
from django.db.models import Count, F
from channels.layers import InMemoryChannelLayer

# Import views' required models and forms from our app
from Meetup.models import (
    Activity, Category, Rating, Comment, IssueReport,
    Conversation, Message, JoinRequest
)
from Meetup.forms import ActivityForm

User = get_user_model()

# Base test class to create and log in a test user
class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user.bio = 'Test bio'
        self.user.save()
        self.client.login(username='testuser', password='testpass')


# ----------------- HOME VIEW -----------------
class HomeViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create a category and two activities with ratings
        self.category = Category.objects.create(name="Sports")
        self.activity1 = Activity.objects.create(
            title="Activity One",
            description="Description 1",
            user=self.user,
            date_time=timezone.now(),
            location="Location 1",
            max_participants=10,
            category=self.category
        )
        self.activity2 = Activity.objects.create(
            title="Activity Two",
            description="Description 2",
            user=self.user,
            date_time=timezone.now(),
            location="Location 2",
            max_participants=10,
            category=self.category
        )
        # Add two ratings to activity1
        Rating.objects.create(activity=self.activity1, user=self.user, score=4, review_text="Good")
        Rating.objects.create(activity=self.activity1, user=self.user, score=5, review_text="Excellent")

    def test_home_view(self):
        """
        Test the home view returns 200, uses the correct template,
        and includes hot activities (with average rating).
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/home.html')
        self.assertIn('hot_activities', response.context)
        hot_activities = response.context['hot_activities']
        # Check that activity1 appears in the hot activities list
        self.assertTrue(any(item['name'] == self.activity1.title for item in hot_activities))


# ----------------- USER PROFILE VIEW -----------------
class UserProfileViewTest(BaseTestCase):
    def test_user_profile_view(self):
        """
        Test userProfile view returns correct profile data.
        """
        response = self.client.get(reverse('userProfile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/profile.html')
        # Check that the response contains the user's username and email
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)


# ----------------- MODIFY PROFILE VIEW -----------------
class ModifyProfileViewTest(BaseTestCase):
    def test_modify_profile_post(self):
        """
        Test that modifyProfile view properly updates the user's information.
        """
        new_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'bio': 'Updated bio',
            'password': 'newpass123'
        }
        response = self.client.post(reverse('modifyProfile'), new_data)
        # Should redirect to userProfile after POST
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.username, 'updateduser')
        self.assertEqual(user.email, 'updated@example.com')
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.bio, 'Updated bio')
        # Logout and try to log in with the new password
        self.client.logout()
        login_success = self.client.login(username='updateduser', password='newpass123')
        self.assertTrue(login_success)


# ----------------- DELETE USER VIEW -----------------
class DeleteUserViewTest(BaseTestCase):
    def test_delete_user_post(self):
        """
        Test that deleteUser view sets the user as inactive and logs them out.
        """
        response = self.client.post(reverse('deleteUser'))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(id=self.user.id)
        self.assertFalse(user.is_active)


# ----------------- ACTIVITIES MANAGEMENT VIEW -----------------
class ActivitiesManageViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create two activities: one owned and one joined
        self.owned_activity = Activity.objects.create(
            title="Owned Activity",
            description="Owned Desc",
            user=self.user,
            date_time=timezone.now(),
            location="Location",
            max_participants=10
        )
        self.joined_activity = Activity.objects.create(
            title="Joined Activity",
            description="Joined Desc",
            user=self.user,
            date_time=timezone.now(),
            location="Location",
            max_participants=10
        )
        self.joined_activity.participants.add(self.user)

    def test_activities_manage_view(self):
        """
        Test that activitiesmanage view returns correct context with pagination.
        """
        response = self.client.get(reverse('activitiesmanage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/activitiesManagement.html')
        # Check that context contains page objects for owned and joined activities
        self.assertIn('my_activities_page_obj', response.context)
        self.assertIn('joined_activities_page_obj', response.context)


# ----------------- ACTIVITIES VIEW -----------------
class ActivitiesViewTest(TestCase):
    def setUp(self):
        """
        Set up a test user and some test activities.
        """
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        self.category = Category.objects.create(name="Music")
        
        # Create test activities with different participant counts
        self.activity1 = Activity.objects.create(
            title="Concert Night",
            description="Live music event",
            user=self.user,
            date_time=timezone.now(),
            location="Music Hall",
            max_participants=5,
            category=self.category
        )

        self.activity2 = Activity.objects.create(
            title="Karaoke Party",
            description="Sing along night",
            user=self.user,
            date_time=timezone.now(),
            location="Karaoke Lounge",
            max_participants=10,
            category=self.category
        )

        self.activity3 = Activity.objects.create(
            title="Piano Recital",
            description="Classical music concert",
            user=self.user,
            date_time=timezone.now(),
            location="Theater",
            max_participants=8,
            category=self.category
        )

        # Simulate participants joining activities
        self.activity1.participants.add(self.user)  # 1/5 full
        self.activity2.participants.add(self.user)  # 1/10 full
        self.activity3.participants.add(self.user)  # 1/8 full
        self.activity3.participants.add(User.objects.create(username="extra_user"))  # 2/8 full

    def test_activities_view_no_filters(self):
        """
        Test activities view returns 200 and correct template when no filters are applied.
        """
        response = self.client.get(reverse('activities'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/activities.html')
        self.assertIn('activities', response.context)

    def test_activities_view_search(self):
        """
        Test activities view filtering by search query.
        """
        response = self.client.get(reverse('activities') + '?q=concert')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Concert Night")
        self.assertNotContains(response, "Karaoke Party")  # Should not show activities that don't match

    def test_activities_view_category_filter(self):
        """
        Test activities view filtering by category.
        """
        response = self.client.get(reverse('activities') + f'?category={self.category.name}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Concert Night")
        self.assertContains(response, "Karaoke Party")

    def test_activities_view_sort_time(self):
        """
        Test activities view sorting by time.
        """
        response = self.client.get(reverse('activities') + '?sort=time')
        self.assertEqual(response.status_code, 200)
        activities = response.context['activities']
        sorted_activities = list(Activity.objects.all().order_by('date_time'))
        self.assertEqual(list(activities), sorted_activities)

    def test_activities_view_sort_almost_full(self):
        """
        Test activities view sorting by fill ratio (Almost full).
        """
        response = self.client.get(reverse('activities') + '?sort=Almost full')
        self.assertEqual(response.status_code, 200)
        activities = response.context['activities']

        # Calculate expected ordering based on fill ratio (participants / max_participants)
        expected_activities = list(
            Activity.objects.annotate(fill_ratio=Count('participants') * 1.0 / F('max_participants'))
            .order_by('-fill_ratio')
        )

        self.assertEqual(list(activities), expected_activities)

# ----------------- ACTIVITY DETAIL VIEW -----------------
class ActivityDetailViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create an activity for detail view test
        self.activity = Activity.objects.create(
            title="Detail Activity",
            description="Activity detail",
            user=self.user,
            date_time=timezone.now(),
            location="Some Location",
            max_participants=20
        )
        # Create a comment for the activity
        Comment.objects.create(
            user=self.user,
            activity=self.activity,
            content="Great activity!"
        )

    def test_activity_detail_view_db(self):
        """
        Test activityDetail view when retrieving from the database.
        """
        response = self.client.get(reverse('ActDetail', args=[self.activity.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/ActDetail.html')
        self.assertContains(response, "Detail Activity")

    def test_activity_detail_view_not_found(self):
        """
        Test activityDetail view returns 404 when activity does not exist.
        """
        response = self.client.get(reverse('ActDetail', args=[9999]))
        self.assertEqual(response.status_code, 404)


# ----------------- MODIFY ACTIVITY VIEW -----------------
class ModifyActivityViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(name="Art")
        self.activity = Activity.objects.create(
            title="Old Title",
            description="Old description",
            user=self.user,
            date_time=timezone.now(),
            location="Old Location",
            max_participants=10,
            category=self.category
        )

    def test_modify_activity_get(self):
        """
        Test modify_activity view GET returns the proper template.
        """
        response = self.client.get(reverse('modifyActivity', args=[self.activity.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/modify_act.html')

    def test_modify_activity_post(self):
        """
        Test modify_activity view POST updates the activity.
        """
        new_data = {
            'title': 'New Title',
            'description': 'New description',
            'category': self.category.id,
            'date_time': '2025-01-01T10:00:00Z',
            'location': 'New Location',
            'max_participants': 20
        }
        response = self.client.post(reverse('modifyActivity', args=[self.activity.id]), new_data)
        # The view renders the template after update with a success message
        self.assertEqual(response.status_code, 200)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.title, 'New Title')
        self.assertEqual(self.activity.description, 'New description')
        self.assertEqual(self.activity.location, 'New Location')
        self.assertEqual(int(self.activity.max_participants), 20)


# ----------------- ADD ACTIVITY VIEW -----------------
class AddActivityViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(name="Theatre")

    # Dummy function to simulate a successful API call for postcode validation
    def dummy_urlopen_success(*args, **kwargs):
        response_data = json.dumps({'result': True})
        return BytesIO(response_data.encode('utf-8'))

    @patch('urllib.request.urlopen', dummy_urlopen_success)
    def test_add_activity_get(self):
        """
        Test GET request to add_activity view returns the proper template.
        """
        response = self.client.get(reverse('add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/add_activity.html')

    @patch('urllib.request.urlopen', dummy_urlopen_success)
    def test_add_activity_post_valid(self):
        """
        Test POST valid data to add_activity view and check for success message.
        """
        valid_data = {
            'title': 'Theatre Play',
            'description': 'A great play',
            'location': '297 Bath St, Glasgow G2 4JN',  # Contains a valid UK postcode
            'date_time': '2025-01-01T10:00:00Z',
            'max_participants': 50,
            'category': self.category.id
        }
        response = self.client.post(reverse('add'), valid_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Activity added successfully" in m.message for m in messages))

    @patch('urllib.request.urlopen', dummy_urlopen_success)
    def test_add_activity_post_invalid_postcode(self):
        """
        Test POST data with invalid postcode so that view returns an error.
        """
        invalid_data = {
            'title': 'Theatre Play',
            'description': 'A great play',
            'location': 'No postcode here',
            'date_time': '2025-01-01T10:00:00Z',
            'max_participants': 50,
            'category': self.category.id
        }
        response = self.client.post(reverse('add'), invalid_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Could not detect a valid UK postcode" in m.message for m in messages))


# ----------------- ACTIVITY REVIEW VIEW -----------------
class ActivityReviewViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.activity = Activity.objects.create(
            title="Review Activity",
            description="Review description",
            user=self.user,
            date_time=timezone.now(),
            location="Review Location",
            max_participants=20
        )

    def test_activity_review_post_valid(self):
        """
        Test valid POST to activity_review view results in creation of a rating.
        """
        post_data = {
            'rating': '4',
            'review_text': 'Excellent activity!'
        }
        response = self.client.post(reverse('activity_review', args=[self.activity.id]), post_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after submission
        rating = Rating.objects.filter(activity=self.activity, user=self.user).first()
        self.assertIsNotNone(rating)
        self.assertEqual(rating.score, 4)
        self.assertEqual(rating.review_text, 'Excellent activity!')

    def test_activity_review_post_invalid_rating(self):
        """
        Test POST to activity_review with invalid rating returns an error message.
        """
        post_data = {
            'rating': '6',  # Out of allowed range (1-5)
            'review_text': 'Invalid rating test'
        }
        response = self.client.post(reverse('activity_review', args=[self.activity.id]), post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid rating" in m.message for m in messages))

    def test_activity_review_post_empty_text(self):
        """
        Test POST to activity_review with empty review text returns an error message.
        """
        post_data = {
            'rating': '3',
            'review_text': ''
        }
        response = self.client.post(reverse('activity_review', args=[self.activity.id]), post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Review text cannot be empty" in m.message for m in messages))


# ----------------- REPORT ISSUE VIEW -----------------
class ReportIssueViewTest(BaseTestCase):
    def test_report_issue_get(self):
        """
        Test GET request to report_issue view returns the correct template.
        """
        response = self.client.get(reverse('report_issue'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/Report.html')

    def test_report_issue_post_valid(self):
        """
        Test POST valid data to report_issue view and check if IssueReport is created.
        """
        post_data = {
            'issue_type': '1',
            'detail': 'There is a bug in the system.'
        }
        response = self.client.post(reverse('report_issue'), post_data)
        self.assertEqual(response.status_code, 302)
        issue = IssueReport.objects.filter(user=self.user).first()
        self.assertIsNotNone(issue)
        self.assertEqual(issue.issue_type, 1)

    def test_report_issue_post_invalid(self):
        """
        Test POST invalid data to report_issue view returns an error message.
        """
        post_data = {
            'issue_type': '',
            'detail': ''
        }
        response = self.client.post(reverse('report_issue'), post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Please select an issue type" in m.message for m in messages))


# ----------------- REGISTER VIEW (CLASS-BASED) -----------------
class RegisterViewTest(TestCase):
    def test_register_get(self):
        """
        Test GET request to the register view returns the correct registration template.
        """
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_register_post(self):
        """
        Test POST to register view creates a new user and redirects.
        """
        post_data = {
            'username': 'newuser',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.filter(username='newuser').first()
        self.assertIsNotNone(new_user)


# ----------------- CHAT HOME VIEW -----------------
class ChatHomeViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create a conversation for the chat home view
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user)
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Hello there",
            timestamp=timezone.now(),
            is_read=False
        )

    def test_chat_home_view(self):
        """
        Test chat_home view returns the correct template with conversation counts.
        """
        response = self.client.get(reverse('chat_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/chat_home.html')
        self.assertIn('conversations_with_counts', response.context)


# ----------------- GET MESSAGES VIEW -----------------
class GetMessagesViewTest(TransactionTestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass')
        
        # Create test conversation
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user)
        
        # Create test message
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Test message",
            timestamp=timezone.now(),
            is_read=False
        )

    def tearDown(self):
        """Clean up after each test."""
        Message.objects.all().delete()
        Conversation.objects.all().delete()
        User.objects.all().delete()

    def test_get_messages_authorized(self):
        """Test get_messages view returns JSON messages for an authorized user."""
        response = self.client.get(reverse('get_messages', args=[self.conversation.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('messages', data)

    def test_get_messages_unauthorized(self):
        """Test get_messages view returns 403 for unauthorized user."""
        # Create a conversation that does not include the logged in user
        conversation2 = Conversation.objects.create()
        response = self.client.get(reverse('get_messages', args=[conversation2.pk]))
        self.assertEqual(response.status_code, 403)


# ----------------- CONVERSATION DETAIL VIEW -----------------
class ConversationDetailViewTest(TransactionTestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        # Create test user and recipient
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass',
            email='other@example.com'
        )
        self.client.login(username='testuser', password='testpass')
        
        # Create test conversation
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user, self.other_user)
        
        # Create test message from other user to test user
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.other_user,  # Message from other user
            content="Test message",
            timestamp=timezone.now(),
            is_read=False
        )

    def tearDown(self):
        """Clean up after each test."""
        Message.objects.all().delete()
        Conversation.objects.all().delete()
        User.objects.all().delete()

    @patch('Meetup.views.get_channel_layer')
    def test_conversation_detail_view(self, mock_get_channel_layer):
        """Test conversation_detail view marks messages as read."""
        # Use a real in-memory channel layer for testing
        mock_channel_layer = InMemoryChannelLayer()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Call the conversation_detail view
        response = self.client.get(reverse('conversation_detail', args=[self.conversation.pk]))
        
        # Check that response status is 200 and correct template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/conversation.html')
        
        # Refresh message from DB and assert that it is now marked as read
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_read)


# ----------------- CREATE CONVERSATION VIEW -----------------
class CreateConversationViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')

    def test_create_conversation_get_with_participant(self):
        """
        Test create_conversation view with participant_id in GET creates or joins a conversation.
        """
        response = self.client.get(reverse('create_conversation') + f'?participant_id={self.other_user.id}')
        self.assertEqual(response.status_code, 302)  # Should redirect to conversation_detail

    def test_create_conversation_get_without_participant(self):
        """
        Test create_conversation view GET without participant_id returns selection template.
        """
        response = self.client.get(reverse('create_conversation'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/create_conversation.html')

    def test_create_conversation_post(self):
        """
        Test create_conversation view POST with participant_id creates a conversation.
        """
        post_data = {'participant_id': self.other_user.id}
        response = self.client.post(reverse('create_conversation'), post_data)
        self.assertEqual(response.status_code, 302)


# ----------------- ADD COMMENT VIEW -----------------
class AddCommentViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.activity = Activity.objects.create(
            title="Comment Test Activity",
            description="Activity for comment testing",
            user=self.user,
            date_time=timezone.now(),
            location="Location",
            max_participants=10
        )

    def test_add_comment_post(self):
        """
        Test add_comment view POST creates a comment and redirects.
        """
        post_data = {'content': 'This is a test comment.'}
        response = self.client.post(reverse('add_comment', args=[self.activity.id]), post_data)
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.filter(activity=self.activity, user=self.user, content='This is a test comment.').first()
        self.assertIsNotNone(comment)


# ----------------- REQUEST TO JOIN VIEW -----------------
class RequestToJoinViewTest(TransactionTestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass')
        
        # Create test activity
        self.activity = Activity.objects.create(
            title="Join Test Activity",
            description="Testing join request",
            user=self.user,
            date_time=timezone.now(),
            location="Location",
            max_participants=1
        )

    def tearDown(self):
        """Clean up after each test."""
        JoinRequest.objects.all().delete()
        Activity.objects.all().delete()
        User.objects.all().delete()

    def test_request_to_join_already_participant(self):
        """Test request_to_join view warns if user is already a participant."""
        self.activity.participants.add(self.user)
        response = self.client.get(reverse('request_to_join', args=[self.activity.pk]))
        self.assertEqual(response.status_code, 302)

    def test_request_to_join_pending_exists(self):
        """Test request_to_join view warns if a pending join request exists."""
        JoinRequest.objects.create(
            user=self.user,
            activity=self.activity,
            status='PENDING'
        )
        response = self.client.get(reverse('request_to_join', args=[self.activity.pk]))
        self.assertEqual(response.status_code, 302)

    def test_request_to_join_activity_full(self):
        """Test request_to_join view returns error if activity is full."""
        other_user = User.objects.create_user(
            username='other',
            password='otherpass'
        )
        self.activity.participants.add(other_user)
        response = self.client.get(reverse('request_to_join', args=[self.activity.pk]))
        self.assertEqual(response.status_code, 302)

    def test_request_to_join_success(self):
        """Test request_to_join view successfully creates a join request."""
        response = self.client.get(reverse('request_to_join', args=[self.activity.pk]))
        self.assertEqual(response.status_code, 302)
        join_req = JoinRequest.objects.filter(
            user=self.user,
            activity=self.activity
        ).first()
        self.assertIsNotNone(join_req)


# ----------------- MANAGE REQUESTS VIEW -----------------
class ManageRequestsViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create an activity owned by the test user
        self.activity = Activity.objects.create(
            title="Manage Requests Activity",
            description="Activity to test manage requests",
            user=self.user,
            date_time=timezone.now(),
            location="Location",
            max_participants=10
        )
        # Create a join request from another user
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        self.join_request = JoinRequest.objects.create(user=self.other_user, activity=self.activity, status='PENDING')

    def test_manage_requests_view(self):
        """
        Test manage_requests view returns the correct template and pending requests.
        """
        response = self.client.get(reverse('manage_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Meetup/manage_requests.html')
        self.assertIn('pending_requests', response.context)
        pending = response.context['pending_requests']
        self.assertTrue(any(jr.user == self.other_user for jr in pending))


# ----------------- HANDLE REQUEST VIEW -----------------
class HandleRequestViewTest(TransactionTestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass')
        
        # Create test activity
        self.activity = Activity.objects.create(
            title="Handle Request Activity",
            description="Activity for handling requests",
            user=self.user,
            date_time=timezone.now(),
            location="Location",
            max_participants=2
        )
        
        # Create other user and join request
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass'
        )
        self.join_request = JoinRequest.objects.create(
            user=self.other_user,
            activity=self.activity,
            status='PENDING'
        )

    def tearDown(self):
        """Clean up after each test."""
        JoinRequest.objects.all().delete()
        Activity.objects.all().delete()
        User.objects.all().delete()

    def test_handle_request_accept(self):
        """Test handle_request view POST with action 'accept'."""
        post_data = {'action': 'accept'}
        response = self.client.post(
            reverse('handle_request', args=[self.join_request.pk]),
            post_data
        )
        self.assertEqual(response.status_code, 302)
        jr = JoinRequest.objects.get(pk=self.join_request.pk)
        self.assertEqual(jr.status, 'ACCEPTED')
        self.assertIn(self.other_user, self.activity.participants.all())

    def test_handle_request_reject(self):
        """Test handle_request view POST with action 'reject'."""
        post_data = {'action': 'reject'}
        response = self.client.post(
            reverse('handle_request', args=[self.join_request.pk]),
            post_data
        )
        self.assertEqual(response.status_code, 302)
        jr = JoinRequest.objects.get(pk=self.join_request.pk)
        self.assertEqual(jr.status, 'REJECTED')
