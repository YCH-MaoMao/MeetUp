// function to update unread count
function updateUnreadCount(conversationId, count) {
    const badge = document.getElementById(`unread-badge-${conversationId}`);
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

// listen for messages from the server about unread counts
const unreadSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/unread_counts/'
);

// update unread count
unreadSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'unread_count_update') {
        updateUnreadCount(data.conversation_id, data.count);
    }
};

// handle socket close
unreadSocket.onclose = function(e) {
    console.error('Unread counts socket closed unexpectedly');
}; 