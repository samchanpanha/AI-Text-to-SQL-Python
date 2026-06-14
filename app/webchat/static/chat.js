const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const sendEl = document.getElementById('send');

let ws = null;

function connect() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat`);

  ws.onopen = () => { console.log('Connected'); };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    // Remove "Thinking..." indicator
    const lastMsg = messagesEl.lastElementChild;
    if (lastMsg && lastMsg.textContent === 'Thinking...') {
      lastMsg.remove();
    }
    addMessage(msg.content, msg.role);
  };

  ws.onclose = () => {
    console.log('Disconnected. Reconnecting in 3s...');
    setTimeout(connect, 3000);
  };
}

function addMessage(text, role) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function send() {
  const text = inputEl.value.trim();
  if (!text || !ws) return;
  inputEl.value = '';
  addMessage('Thinking...', 'thinking');
  ws.send(JSON.stringify({ content: text }));
}

sendEl.addEventListener('click', send);
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') send();
});

connect();
