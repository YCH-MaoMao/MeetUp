from .models import Message

def unread_messages_count(request):
    """
    This context processor provides the count of unread messages for the current user in all templates.
    
    The count includes messages that:
    - are in any conversation where the current user is a participant
    - messages that have not been read
    - were not sent by the current user
    """
    if request.user.is_authenticated:
        # Count the unread messages for the current user
        unread_count = Message.objects.filter(
            conversation__participants=request.user,  # Messages in user's conversations
            is_read=False  # checks for only unread messages
        ).exclude(sender=request.user).count()  # excludes any messages sent by the current user
        return {'unread_messages': unread_count}
    
    # Return 0 unread messages for non-authenticated users
    return {'unread_messages': 0} 