from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.paginator import Paginator
from .forms import ActivityForm
from django.contrib import messages
from django.db.models import Avg,Count, F
from .models import Category, Activity, Rating, IssueReport, Conversation, Message, Comment, JoinRequest
import json
from django.utils.dateparse import parse_datetime
import urllib.request
import re
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

# home page 
def home(request):
    # Get top 6 activities by average rating
    activities = Activity.objects.annotate(avg_rating=Avg('rating__score')).order_by('-avg_rating')[:6]

    # Convert to dictionary for template usage
    hot_activities = [
        {'id': activity.id, 'name': activity.title, 'rating': round(activity.avg_rating, 1) if activity.avg_rating else "N/A"}
        for activity in activities
    ]

    context_dict = {
        'hot_activities': hot_activities
    }
    return render(request, 'Meetup/home.html', context=context_dict)

# user profile page
@login_required
def userProfile(request):
    user = request.user
    profile_data = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'bio': user.bio,
    }
    return render(request, 'Meetup/profile.html', context = profile_data)

# modify user profile page
@login_required
def modifyProfile(request):
    user = request.user

    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.bio = request.POST.get('bio', user.bio)
        
        if request.POST.get('password'):
            user.set_password(request.POST['password'])
        
        user.save()
        
    return redirect('userProfile')

# delete user page
@login_required
def deleteUser(request):
    user = request.user

    if request.method == 'POST':
        print(f"Disabling user: {user.username}")
        user.is_active = False
        user.save()
        logout(request)
    
    return redirect("login")

# activities management page
@login_required
def activitiesmanage(request):
    #filter out the activities created by user
    activities = Activity.objects.filter(user=request.user).order_by('date_time')
    my_activities = [{'id': activity.id, 'name': activity.title} for activity in activities]
    
    joined_activities = Activity.objects.filter(participants=request.user).order_by('date_time').all()
    joined_activities = [{'id': activity.id, 'name': activity.title} for activity in joined_activities]
    
    my_activities_paginator = Paginator(my_activities, 10)  
    joined_activities_paginator = Paginator(joined_activities, 10)  
    
    my_activities_page_number = request.GET.get('my_activities_page')
    joined_activities_page_number = request.GET.get('joined_activities_page')
    
    my_activities_page_obj = my_activities_paginator.get_page(my_activities_page_number)
    joined_activities_page_obj = joined_activities_paginator.get_page(joined_activities_page_number)
    
    context_dict = {
        'my_activities_page_obj': my_activities_page_obj,
        'joined_activities_page_obj': joined_activities_page_obj,
    }
    return render(request, 'Meetup/activitiesManagement.html', context=context_dict)

# activities page
@login_required
def activities(request):
    search_query = request.GET.get("q", "").strip().lower()
    sort_option = request.GET.get("sort", "")
    category_filter = request.GET.get("category", "")
    
    categories = Category.objects.all()
    
    activities_list = Activity.objects.all()

    # search (in title, description, date_time)
    if search_query:
        activities_list = activities_list.filter(
            title__icontains=search_query
        ) | activities_list.filter(
            description__icontains=search_query
        ) | activities_list.filter(
            date_time__icontains=search_query
        )

    # filter out activities by category
    if category_filter:
        Category_id=Category.objects.filter(name__iexact=category_filter).first().id
        activities_list = activities_list.filter(category__id=Category_id)

    # order activities by date_time
    if sort_option == "time":
        activities_list = activities_list.order_by("date_time")  # from old to latest
    elif sort_option == "Almost full":
        activities_list = activities_list.annotate(
            fill_ratio=Count('participants') * 1.0 / F('max_participants')
        ).order_by('-fill_ratio')

    # paginate activities
    paginator = Paginator(activities_list, 5)
    page_number = request.GET.get("page")
    activities_page = paginator.get_page(page_number)

    # render activities page
    return render(request, 'Meetup/activities.html', {
        'activities': activities_page,
        'category_list': categories,
        'selected_category': category_filter,
        'selected_sort': sort_option,
        'search_query': search_query,
    })

# activity detail page
@login_required
def activityDetail(request, activity_id):
    try:
        activity = Activity.objects.get(id=activity_id)
        activity_data = {
            'id': activity.id,
            'name': activity.title,
            'description': activity.description,
            'location': activity.location,
            'date_time': activity.date_time,
            'user_id': activity.user.id,  # Add user ID to activity data
            'max_participants': activity.max_participants,  # Add max_participants
            'title': activity.title,  # Add title since we use it in the template
            'participants': activity.participants,  # Add participants
            'user': activity.user  # Add user object for template comparison
        }
        comments = Comment.objects.filter(activity=activity).order_by('-timestamp')
        # render activity detail page
        return render(request, 'Meetup/ActDetail.html', {
            'activity': activity_data,
            'comments': comments
        })
    except Activity.DoesNotExist:
        return HttpResponse("No Activity matches the given query.", status=404)
    except Exception as e:
        print(f"Error loading activity from database: {e}")
        return HttpResponse("Error loading activity", status=500)

# modify activity page
@login_required
def modify_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    categories = Category.objects.all()
    # update activity data
    if request.method == "POST":
        activity.title = request.POST.get("title", activity.title)
        activity.description = request.POST.get("description", activity.description)
        activity.category = get_object_or_404(Category, id=request.POST.get("category")) if request.POST.get("category") else None
        activity.date_time = parse_datetime(request.POST.get("date_time")) if request.POST.get("date_time") else activity.date_time
        activity.location = request.POST.get("location", activity.location)
        activity.max_participants = request.POST.get("max_participants", activity.max_participants)
        
        activity.save()
        messages.success(request, 'Activity updated successfully!')
        
    # render modify activity page
    return render(request, 'Meetup/modify_act.html',
                  {
                      'activity': activity,
                      'categories':categories
                   })

# extract postcode from address
def extract_postcode(address):
    postcode_pattern = r"\b[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2}\b"
    match = re.search(postcode_pattern, address, re.IGNORECASE)
    return match.group(0).strip() if match else None

@login_required
def add_activity(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            # validate UK postcode using postcodes.io API
            
            address = form.cleaned_data.get("location", "").strip()
            postcode = extract_postcode(address)
            
            if not postcode:
                messages.error(request, "Could not detect a valid UK postcode in your address. Please enter a full UK address including the postcode.")
                return render(request, 'Meetup/add_activity.html', {'form': form, 'categories': categories})
  
            #get the last part as postcode
            encoded_postcode = urllib.parse.quote(postcode)
            api_url = f"https://api.postcodes.io/postcodes/{encoded_postcode}/validate"

            print(api_url)
            try:
                with urllib.request.urlopen(api_url) as response:
                    data = json.loads(response.read().decode())

                    # check if postcode is valid
                    if not data.get('result', False):
                        messages.error(request, "Invalid UK postcode. Please enter a valid one.")
                        return render(request, 'Meetup/add_activity.html', {'form': form, 'categories': categories})

            except Exception as e:
                messages.error(request, "Error validating postcode. Please try again.")
                return render(request, 'Meetup/add_activity.html', {'form': form, 'categories': categories})

            # save activity
            activity = form.save(commit=False)
            activity.user = request.user
            activity.save()
            
            # Add the creator as a participant
            activity.participants.add(request.user)
            activity.save()
            
            messages.success(request, 'Activity added successfully!')

        else:
            messages.error(request, 'Failed to add activity. Please correct the errors below.')

    # render add activity page
    else:
        form = ActivityForm()

    return render(request, 'Meetup/add_activity.html', {'form': form, 'categories': categories})

# activity review page  
@login_required
def activity_review(request, id):
    # Retrieve the activity, or return 404 if not found
    activity = get_object_or_404(Activity, id=id)
    
    if request.method == "POST":
        rating = request.POST.get("rating")
        review_text = request.POST.get("review_text", "").strip()

        # Validate rating input (must be a number between 1 and 5)
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating. Please select a value between 1 and 5.")
            return redirect("activity_review", id=id)

        # check if review text is empty
        if not review_text:
            messages.error(request, "Review text cannot be empty.")
            return redirect("activity_review", id=id)

        # check if the user already reviewed this activity
        review, created = Rating.objects.get_or_create(
            activity=activity,
            user=request.user,
            defaults={"score": rating, "review_text": review_text}
        )

        if not created:
            # update existing review
            review.score = rating
            review.review_text = review_text
            review.save()
            messages.success(request, "Your review has been updated.")
        else:
            messages.success(request, "Your review has been submitted.")

        return redirect("activity_review", id=id)

    # fetch existing reviews for display
    reviews = Rating.objects.filter(activity=activity).select_related("user").first()  # Optimized Query
    
    return render(request, "Meetup/activity_review.html", {
        "activity": activity,
        "reviews": reviews,
    })

# report issue page
@login_required
def report_issue(request):
    # define issue type choices in views.py
    ISSUE_CHOICES = {
        1: "Bug Report",
        2: "Feedback",
        3: "Suggestion",
        4: "Other",
    }
    if request.method == "POST":
        issue_type = request.POST.get("issue_type")
        detail = request.POST.get("detail").strip()

        # check if issue type and detail are provided
        if not issue_type or not detail:
            messages.error(request, "Please select an issue type and provide details.")
            return render(request, "Meetup/Report.html", {"ISSUE_CHOICES": ISSUE_CHOICES})

        try:
            issue_type = int(issue_type)  # Convert to integer
            if issue_type not in ISSUE_CHOICES:
                raise ValueError  # Invalid selection
        except ValueError:
            messages.error(request, "Invalid issue type selected.")
            return render(request, "Meetup/Report.html", {"ISSUE_CHOICES": ISSUE_CHOICES})

        # save issue report
        IssueReport.objects.create(user=request.user, issue_type=issue_type, detail=detail)

        messages.success(request, "Your report has been submitted successfully.")
        return redirect("report_issue")  # prevent form resubmission

    # render report issue page
    return render(request, "Meetup/Report.html", {"ISSUE_CHOICES": ISSUE_CHOICES})

# custom user creation form
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields

# register view
class RegisterView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

# chat home page
@login_required
def chat_home(request):
    conversations = Conversation.objects.filter(participants=request.user)
    # add unread message counts for each conversation
    conversations_with_counts = []
    for conversation in conversations:
        unread_count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).count()
        conversations_with_counts.append({
            'conversation': conversation,
            'unread_count': unread_count
        })
    
    # render chat home page
    return render(request, 'Meetup/chat_home.html', {
        'conversations_with_counts': conversations_with_counts
    })

# conversation detail page
@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.all().order_by('timestamp')
    
    # mark messages as read
    unread_messages = conversation.messages.filter(is_read=False).exclude(sender=request.user)
    unread_messages.update(is_read=True)
    
    # broadcast unread count update
    channel_layer = get_channel_layer()
    unread_count = conversation.messages.filter(is_read=False).exclude(sender=request.user).count()
    async_to_sync(channel_layer.group_send)(
        "unread_counts",
        {
            "type": "unread_count_update",
            "conversation_id": conversation_id,
            "count": unread_count
        }
    )
    
    # render conversation detail page
    return render(request, 'Meetup/conversation.html', {
        'conversation': conversation,
        'messages': messages
    })

# create conversation page
@login_required
def create_conversation(request):
    # get participant_id from URL if it exists
    participant_id = request.GET.get('participant_id')
    if participant_id:
        # if participant_id is provided, automatically create/join conversation
        other_user = get_object_or_404(User, id=participant_id)
        # check if conversation already exists
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, other_user)
        
        return redirect('conversation_detail', conversation_id=conversation.id)
    
    # handle POST request for manual conversation creation
    if request.method == 'POST':
        participant_id = request.POST.get('participant_id')
        if participant_id:
            other_user = get_object_or_404(User, id=participant_id)
            # check if conversation already exists
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=other_user
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, other_user)
            
            return redirect('conversation_detail', conversation_id=conversation.id)
    
    # if no participant_id, show the user selection page
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'Meetup/create_conversation.html', {'users': users})

@login_required
def get_messages(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # mark any new unread messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    messages = conversation.messages.order_by('-timestamp')[:50]
    message_list = [{
        'id': message.id,
        'content': message.content,
        'sender': message.sender.username,
        'timestamp': message.timestamp.isoformat(),
        'is_read': message.is_read
    } for message in messages]
    
    # return messages   
    return JsonResponse({'messages': message_list})

# add comment page
@login_required
def add_comment(request, activity_id):
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)

        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                user=request.user,
                activity=activity,
                content=content
            )
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Comment cannot be empty!')
            
    # redirect to activity detail page
    return redirect('ActDetail', activity_id=activity_id)

# request to join page
@login_required
def request_to_join(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    
    # check if user is already a participant    
    if request.user in activity.participants.all():
        messages.warning(request, 'You are already a participant in this activity.')
        return redirect('ActDetail', activity_id=activity_id)
    
    # check if there's already a pending request
    existing_request = JoinRequest.objects.filter(
        user=request.user,
        activity=activity,
        status='PENDING'
    ).exists()
    
    if existing_request:
        messages.warning(request, 'You already have a pending request for this activity.')
        return redirect('ActDetail', activity_id=activity_id)
    
    # check if activity is full
    current_participants = activity.participants.count()
    if current_participants >= activity.max_participants:
        messages.error(request, 'This activity is already full.')
        return redirect('ActDetail', activity_id=activity_id)
    
    # create join request
    JoinRequest.objects.create(
        user=request.user,
        activity=activity
    )
    
    messages.success(request, 'Your request to join has been sent.')
    return redirect('ActDetail', activity_id=activity_id)

# manage requests page
@login_required
def manage_requests(request):
    # get activities created by the user
    user_activities = Activity.objects.filter(user=request.user)
    
    # get pending requests for all user's activities
    pending_requests = JoinRequest.objects.filter(
        activity__in=user_activities,
        status='PENDING'
    ).select_related('user', 'activity')
    
    # render manage requests page
    return render(request, 'Meetup/manage_requests.html', {
        'pending_requests': pending_requests
    })

# handle request page
@login_required
def handle_request(request, request_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    join_request = get_object_or_404(JoinRequest, id=request_id)
    activity = join_request.activity
    
    # verify the current user is the activity owner
    if activity.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    action = request.POST.get('action')
    
    if action == 'accept':
        # check if activity is full before accepting
        current_participants = activity.participants.count()
        if current_participants >= activity.max_participants:
            join_request.status = 'REJECTED'
            join_request.save()
            messages.error(request, 'Cannot accept request: Activity is full')
        else:
            join_request.status = 'ACCEPTED'
            join_request.save()
            activity.participants.add(join_request.user)
            messages.success(request, f'Accepted {join_request.user.username} to the activity')
    
    elif action == 'reject':
        join_request.status = 'REJECTED'
        join_request.save()
        messages.success(request, f'Rejected {join_request.user.username}\'s request')
    
    # redirect to manage requests page
    return redirect('manage_requests')