// 1. HTML 요소 가져오기
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');

// 2. 페이지 로드 시 이전 대화 기록 불러오기
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/chat-histories/activities/'); // GET 요청으로 히스토리 API 호출
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
});


// 3. 메시지 전송 함수
const sendMessage = async () => {
    const messageText = chatInput.value.trim();
    if (messageText === '') return; // 입력 내용이 없으면 전송 안 함

    // 사용자 메시지를 화면에 먼저 표시
    addMessage('query', messageText);
    chatInput.value = '';

    try {
        // 챗봇 API에 메시지 전송
        const response = await fetch('/api/activities_recommendation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken // CSRF 토큰 추가
            },
            body: JSON.stringify({ message: messageText })
        });

        if (!response.ok) throw new Error('챗봇 응답을 가져오는 데 실패했습니다.');

        const data = await response.json();
        const botResponseText = data.response;

        // 봇 응답을 화면에 표시
        addMessage('response', botResponseText);

        // 대화 기록 저장 API 호출
        await saveHistory(messageText, botResponseText);

    } catch (error) {
        console.error(error);
        addMessage('bot', '죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.');
    }
};

// 4. 대화 기록 저장 함수
const saveHistory = async (query, response) => {
    try {
        await fetch('/api/chat-histories/activities/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken // CSRF 토큰 추가
            },
            body: JSON.stringify({
                query: query,
                response: response
            })
        });
    } catch (error) {
        console.error('대화 기록 저장 실패:', error);
    }
};


// 5. 화면에 말풍선 추가하는 함수
const addMessage = (sender, text) => {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender); 

    const bubbleElement = document.createElement('div');
    bubbleElement.classList.add('bubble');
    bubbleElement.textContent = text;

    messageElement.appendChild(bubbleElement);
    chatMessages.appendChild(messageElement);

    // 스크롤을 항상 맨 아래로 이동
    chatMessages.scrollTop = chatMessages.scrollHeight;
};


// 6. 이벤트 리스너 연결 (클릭 또는 Enter 키로 메시지 전송)
sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});