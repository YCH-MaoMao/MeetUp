// Initialize the WebSocket connection
const conversationId = document.getElementById('conversation-id').dataset.id;
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + conversationId + '/'
);

// Handle incoming messages
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    const isCurrentUser = data.sender_username === document.getElementById('current-user').dataset.username;
    // Create a new message element with the appropriate class based on the sender
    messageDiv.className = `message ${isCurrentUser ? 'sent' : 'received'}`;
    // Add the message content and metadata to the new message element
    messageDiv.innerHTML = `
        <div class="message-content">${data.message}</div>
        <div class="message-meta">
            ${data.sender_username} - ${new Date(data.timestamp).toLocaleTimeString()}
        </div>
    `;
    // Append the new message element to the messages container
    messagesContainer.appendChild(messageDiv);
    // Scroll to the bottom of the messages container
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
};

// Handle the closing of the WebSocket connection
chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

// Focus on the message input when the page loads
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#chat-message-input').focus();
    
    // Handle the enter key in the message input
    document.querySelector('#chat-message-input').onkeyup = function(e) {
        if (e.keyCode === 13) {  // enter key
            document.querySelector('#chat-message-submit').click();
        }
    };
    
    // Handle the send button click
    document.querySelector('#chat-message-submit').onclick = function(e) {
        const messageInputDom = document.querySelector('#chat-message-input');
        const message = messageInputDom.value;
        if (message.trim()) {
            chatSocket.send(JSON.stringify({
                'message': message
            }));
            messageInputDom.value = '';
        }
    };
    
    // Scroll to the bottom of the messages container on load
    const messagesContainer = document.getElementById('messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}); 