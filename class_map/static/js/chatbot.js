
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');

// 화면에 말풍선을 추가하고 스크롤을 내리는 함수
const addMessage = (sender, text) => {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    const bubbleElement = document.createElement('div');
    bubbleElement.classList.add('bubble');
    bubbleElement.textContent = text;

    messageElement.appendChild(bubbleElement);
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
};

// 대화 기록을 서버에 저장하는 함수
const saveHistory = async (query, response) => {
    const accessToken = localStorage.getItem('access');
    if (!accessToken) return;

    try {
        await fetch('/api/chat-histories/activities/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ query: query, response: response })
        });
    } catch (error) {
        console.error('대화 기록 저장 실패:', error);
    }
};

// 메시지를 전송하고 챗봇 응답을 받는 메인 함수
const sendMessage = async () => {
    const messageText = chatInput.value.trim();
    if (messageText === '') return;

    addMessage('query', messageText);
    chatInput.value = '';

    const accessToken = localStorage.getItem('access');
    if (!accessToken) {
        alert('인증 정보가 없습니다. 다시 로그인해주세요.');
        return;
    }

    try {
        const response = await fetch('/api/activities-recommendation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ message: messageText })
        });

        if (!response.ok) {
            throw new Error('챗봇 응답을 가져오는 데 실패했습니다.');
        }

        const data = await response.json();
        const botResponseText = data.response;

        addMessage('response', botResponseText);
        await saveHistory(messageText, botResponseText);

    } catch (error) {
        console.error(error);
        addMessage('response', '죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.');
    }
};

// 페이지가 처음 로드될 때 이전 대화 기록을 불러오는 함수
const loadInitialHistory = async () => {
    const accessToken = localStorage.getItem('access');
    if (!accessToken) {
        alert('인증 정보가 없습니다. 로그인 페이지로 이동합니다.');
        window.location.href = '/login/';
        return;
    }

    try {
        const response = await fetch('/api/chat-histories/activities/', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });

        if (response.status === 401) {
            alert('인증이 만료되었습니다. 다시 로그인해주세요.');
            window.location.href = '/login/';
            return;
        }

        if (!response.ok) throw new Error('대화 기록을 불러오는 데 실패했습니다.');
        
        const histories = await response.json();
        histories.forEach(item => {
            addMessage('query', item.query);
            addMessage('response', item.response);
        });

    } catch (error) {
        console.error(error);
        addMessage('response', '이전 대화 기록을 불러오는 중 오류가 발생했습니다.');
    }
};

// --- 이벤트 리스너 연결 ---
// 페이지가 로드되면 히스토리 불러오기 실행
window.addEventListener('load', loadInitialHistory);

// 버튼 클릭 또는 Enter 키로 메시지 전송
sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});