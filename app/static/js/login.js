document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('error-message');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                }),
                credentials: 'include'  // 쿠키를 포함하기 위해 필요
            });

            const data = await response.json();

            if (response.ok) {
                // 로그인 성공 시 메인 페이지로 이동
                window.location.href = '/';
            } else {
                // 에러 메시지 표시
                errorMessage.textContent = data.detail || '로그인에 실패했습니다.';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('로그인 중 오류 발생:', error);
            errorMessage.textContent = '로그인 처리 중 오류가 발생했습니다.';
            errorMessage.style.display = 'block';
        }
    });
}); 