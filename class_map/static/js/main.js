// ==== main.html에 필요한 js 스크립트 ====

document.getElementById('activities-chatbot-card').addEventListener('click', () => {
    const accessToken = localStorage.getItem('access');
    console.log("access token: ", accessToken);
    if (accessToken) {
        window.location.href = '/chatbot/'; 
    } else {
        alert('로그인이 필요한 기능입니다.');
        window.location.href = '/login/'; 
    }
});