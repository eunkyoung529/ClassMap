
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const resultsContainer = document.getElementById('results-container');
const loadingSpinner = document.getElementById('loading-spinner');

/**
 * 검색 결과 배열을 받아 HTML로 변환하여 화면에 표시하는 함수
 * @param {Array} results - 서버로부터 받은 검색 결과 객체들의 배열
 */
const renderResults = (results) => {
    // 검색 결과가 없을 경우 사용자에게 알려줌
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<p class="placeholder-text">검색 결과가 없습니다.</p>';
        return;
    }

    // map 함수를 사용해 각 결과 객체를 HTML 카드 문자열로 변환하고,
    // join('')으로 모든 카드들을 하나의 긴 문자열로 합친다
    const resultsHTML = results.map(review => `
        <div class="result-card">
            <div class="card-header">
                <h3 class="title">${review.title}</h3>
                <p class="meta-info">${review.professor} · ${review.semester}</p>
            </div>
            <div class="card-content">
                <p>${review.content}</p>
            </div>
        </div>
    `).join('');

    // 생성된 HTML을 결과 컨테이너에 삽입
    resultsContainer.innerHTML = resultsHTML;
};


/**
 * 검색어를 가지고 API를 호출하여 결과를 가져오는 메인 함수
 */
const performSearch = async () => {
    const query = searchInput.value.trim();

    // 검색어가 비어있으면 사용자에게 알린다
    if (!query) {
        resultsContainer.innerHTML = '<p class="placeholder-text">검색어를 입력해주세요.</p>';
        return;
    }

    // 검색을 시작하기 전에 로딩 스피너를 보여주고, 이전 결과는 지운다
    loadingSpinner.classList.remove('hidden');
    resultsContainer.innerHTML = '';

    try {
        const accessToken = localStorage.getItem('access');

        if (!accessToken) {
            throw new Error('로그인이 필요합니다. 먼저 로그인해주세요.');
        }

        const response = await fetch(
            `/api/search/?q=${encodeURIComponent(query)}`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                }
            }
        );

        if (response.status === 401) {
             throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
        }
        if (!response.ok) {
            throw new Error('데이터를 불러오는 중 서버에 오류가 발생했습니다.');
        }

        const data = await response.json();
        renderResults(data.results);

    } catch (error) {
        // fetch 과정에서 발생한 모든 오류(네트워크 오류, 인증 오류 등)를 여기서 처리
        console.error('Search API Error:', error);
        resultsContainer.innerHTML = `<p class="placeholder-text">오류가 발생했습니다: ${error.message}</p>`;
    } finally {
        // 로딩 스피너를 숨기기
        loadingSpinner.classList.add('hidden');
    }
};


searchButton.addEventListener('click', performSearch);

searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault(); // form 태그 안에서 Enter를 눌렀을 때 페이지가 새로고침되는 것을 방지
        performSearch();
    }
});
