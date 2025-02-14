document.addEventListener('DOMContentLoaded', function() {
    // 랜덤 아바타 이미지 설정
    const avatarNumber = Math.floor(Math.random() * 5) + 1;
    document.documentElement.style.setProperty('--avatar-image', `url('/static/images/avatar_${avatarNumber}.png')`);

    // 로그아웃 버튼 이벤트 리스너
    const logoutButton = document.querySelector('.logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', async function() {
            try {
                const response = await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        ...securityManager.addSecurityHeaders(),
                        'Authorization': `Bearer ${api.authToken}`
                    }
                });
                if (response.ok) {
                    api.clearAuthToken();
                    window.location.href = '/login';
                } else {
                    throw new Error('로그아웃 실패');
                }
            } catch (error) {
                console.error('로그아웃 오류:', error);
                showNotification('오류', '로그아웃 중 오류가 발생했습니다.', 'error');
            }
        });
    }

    let ws = null;
    let selectedCamera = 'all';
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    const RECONNECT_DELAY = 1000; // 1초

    // 웹소켓 상태 표시 함수
    function updateConnectionStatus(status) {
        const statusElement = document.querySelector('.connection-status');
        if (!statusElement) {
            const header = document.querySelector('.div-4');
            const statusDiv = document.createElement('div');
            statusDiv.className = 'connection-status';
            header.appendChild(statusDiv);
        }
        const element = document.querySelector('.connection-status');
        element.textContent = status;
        element.className = `connection-status ${status.toLowerCase()}`;
    }

    // WebSocket 연결 설정
    function setupWebSocket() {
        if (ws) {
            ws.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/ws`;
        
        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('WebSocket 연결됨');
            updateConnectionStatus('연결됨');
            reconnectAttempts = 0;
        };

        ws.onclose = function() {
            console.log('WebSocket 연결 끊김');
            updateConnectionStatus('연결 실패');
            
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                setTimeout(setupWebSocket, RECONNECT_DELAY * reconnectAttempts);
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket 오류:', error);
            updateConnectionStatus('연결 오류');
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            // 메시지 처리 로직
            console.log('받은 메시지:', data);
        };
    }

    // 알림 드롭다운 관리
    const notificationButton = document.getElementById('notificationButton');
    const notificationDropdown = document.querySelector('.notification-dropdown');
    const notificationList = document.querySelector('.notification-list');
    const clearAllButton = document.querySelector('.clear-all');
    const notificationBackdrop = document.getElementById('notificationBackdrop');
    let notifications = [];
    let isNotificationVisible = false;

    if (notificationButton && notificationDropdown) {
        // 알림 버튼 클릭 이벤트
        notificationButton.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            isNotificationVisible = !isNotificationVisible;
            toggleNotificationDropdown(isNotificationVisible);
            
            // 알림 표시 제거
            if (isNotificationVisible) {
                const indicator = notificationButton.querySelector('.span-2');
                if (indicator) {
                    indicator.style.display = 'none';
                }
            }
        });

        // 문서 클릭시 드롭다운 닫기
        document.addEventListener('click', (event) => {
            // 알림 버튼이나 드롭다운 내부를 클릭한 경우가 아닐 때만 닫기
            if (!event.target.closest('.notification-dropdown') && 
                !event.target.closest('#notificationButton')) {
                isNotificationVisible = false;
                toggleNotificationDropdown(false);
            }
        });

        // ESC 키로 드롭다운 닫기
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && isNotificationVisible) {
                isNotificationVisible = false;
                toggleNotificationDropdown(false);
            }
        });

        // 모두 지우기 버튼 클릭 이벤트
        if (clearAllButton) {
            clearAllButton.addEventListener('click', () => {
                notifications = [];
                updateNotificationList();
            });
        }
    }

    // 알림 드롭다운 토글
    function toggleNotificationDropdown(show) {
        notificationDropdown.style.display = show ? 'block' : 'none';
        notificationBackdrop.style.display = show ? 'block' : 'none';
        if (show) {
            updateNotificationList();
        }
    }

    // 알림 목록 업데이트
    function updateNotificationList() {
        if (!notificationList) return;
        
        notificationList.innerHTML = '';
        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="notification-item">
                    <div class="notification-content">
                        <div class="notification-message">새로운 알림이 없습니다.</div>
                    </div>
                </div>`;
            return;
        }

        notifications.forEach((notification) => {
            const notificationItem = document.createElement('div');
            notificationItem.className = 'notification-item';
            notificationItem.innerHTML = `
                <i class="material-icons">${notification.type === 'error' ? 'error' : 'warning'}</i>
                <div class="notification-content">
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${notification.time}</div>
                </div>
            `;
            notificationList.appendChild(notificationItem);
        });
    }

    // 알림 추가 함수 수정
    function showNotification(title, message, type = 'info') {
        // 기존 토스트 알림 표시
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 500);
        }, 5000);

        // 알림 목록에 추가
        notifications.unshift({
            title,
            message,
            type,
            time: new Date().toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit'
            })
        });

        // 최대 10개까지만 유지
        if (notifications.length > 10) {
            notifications.pop();
        }

        // 알림 표시 업데이트
        const indicator = notificationButton.querySelector('.span-2');
        if (indicator) {
            indicator.style.display = 'block';
        }

        // 알림 목록 업데이트
        updateNotificationList();
    }

    // 보안 관리 클래스
    class SecurityManager {
        constructor() {
            this.inactivityTimer = null;
            this.lastActivity = Date.now();
            this.isLocked = false;
            this.initializeSecurityFeatures();
        }

        // 보안 기능 초기화
        initializeSecurityFeatures() {
            // XSS 방지를 위한 이스케이프 함수 정의
            this.escapeHtml = (unsafe) => {
                return unsafe
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            };

            // 활동 감지 이벤트 리스너
            ['mousemove', 'keydown', 'mousedown', 'touchstart'].forEach(eventType => {
                document.addEventListener(eventType, () => this.resetInactivityTimer());
            });

            // 우클릭 방지
            document.addEventListener('contextmenu', (e) => {
                if (!this.isDevelopmentMode()) {
                    e.preventDefault();
                }
            });

            // 개발자 도구 감지
            this.detectDevTools();
        }

        // 개발 모드 확인
        isDevelopmentMode() {
            return window.location.hostname === 'localhost' || 
                   window.location.hostname === '127.0.0.1';
        }

        // 개발자 도구 감지
        detectDevTools() {
            const handler = () => {
                if (!this.isDevelopmentMode()) {
                    showNotification(
                        '보안 경고',
                        '개발자 도구 사용이 감지되었습니다.',
                        'warning'
                    );
                }
            };

            // Chrome, Firefox
            window.addEventListener('devtoolschange', handler);
            
            // 다양한 개발자 도구 감지 방법
            setInterval(() => {
                const widthThreshold = window.outerWidth - window.innerWidth > 160;
                const heightThreshold = window.outerHeight - window.innerHeight > 160;
                if (!this.isDevelopmentMode() && (widthThreshold || heightThreshold)) {
                    handler();
                }
            }, 1000);
        }

        // 비활성 타이머 재설정
        resetInactivityTimer() {
            this.lastActivity = Date.now();
            if (this.isLocked) {
                this.unlock();
            }
        }

        // 화면 잠금
        lock() {
            if (!this.isLocked) {
                this.isLocked = true;
                this.showLockScreen();
            }
        }

        // 화면 잠금 해제
        unlock() {
            if (this.isLocked) {
                this.isLocked = false;
                this.hideLockScreen();
            }
        }

        // 잠금 화면 표시
        showLockScreen() {
            const lockScreen = document.createElement('div');
            lockScreen.id = 'security-lock-screen';
            lockScreen.className = 'security-lock-screen';
            lockScreen.innerHTML = `
                <div class="lock-content">
                    <i class="material-icons">lock</i>
                    <h2>화면이 잠겼습니다</h2>
                    <p>아무 키나 누르거나 마우스를 움직여서 잠금을 해제하세요.</p>
                </div>
            `;
            document.body.appendChild(lockScreen);
        }

        // 잠금 화면 제거
        hideLockScreen() {
            const lockScreen = document.getElementById('security-lock-screen');
            if (lockScreen) {
                lockScreen.remove();
            }
        }

        // 문자열 이스케이프 처리
        sanitizeInput(input) {
            if (typeof input !== 'string') return input;
            return this.escapeHtml(input);
        }

        // API 요청 보안 헤더 추가
        addSecurityHeaders(headers = {}) {
            return {
                ...headers,
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block'
            };
        }

        // CSRF 토큰 관리
        getCsrfToken() {
            return document.querySelector('meta[name="csrf-token"]')?.content;
        }

        // 보안 로그 기록
        logSecurityEvent(event) {
            console.warn('보안 이벤트:', event);
            // 서버에 보안 이벤트 로깅
            api.post('/api/v1/security/log', {
                event_type: event.type,
                details: event.details,
                timestamp: new Date().toISOString()
            }).catch(error => {
                console.error('보안 로그 기록 실패:', error);
                // 실패해도 계속 진행
            });
        }
    }

    // 보안 매니저 인스턴스 생성
    const securityManager = new SecurityManager();

    // API 요청 설정
    const API_CONFIG = {
        BASE_URL: '',  // BASE_URL을 빈 문자열로 설정
        MAX_RETRIES: 3,
        RETRY_DELAY: 1000,
        TIMEOUT: 10000
    };

    // API 클라이언트 클래스
    class ApiClient {
        constructor(config = API_CONFIG) {
            this.config = config;
            this.pendingRequests = new Map();
            this.authToken = this.getStoredAuthToken();
        }

        // 저장된 인증 토큰 가져오기
        getStoredAuthToken() {
            return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        }

        // 인증 토큰 저장
        setAuthToken(token, remember = false) {
            if (remember) {
                localStorage.setItem('authToken', token);
            } else {
                sessionStorage.setItem('authToken', token);
            }
            this.authToken = token;
        }

        // 인증 토큰 제거
        clearAuthToken() {
            localStorage.removeItem('authToken');
            sessionStorage.removeItem('authToken');
            this.authToken = null;
        }

        // API 요청 실행
        async request(endpoint, options = {}) {
            const requestKey = `${options.method || 'GET'}_${endpoint}`;
            
            // 중복 요청 방지
            if (this.pendingRequests.has(requestKey)) {
                return this.pendingRequests.get(requestKey);
            }

            const requestPromise = this._executeRequest(endpoint, options);
            this.pendingRequests.set(requestKey, requestPromise);

            try {
                const response = await requestPromise;
                return response;
            } finally {
                this.pendingRequests.delete(requestKey);
            }
        }

        // 실제 API 요청 실행
        async _executeRequest(endpoint, options = {}) {
            let lastError;
            const url = `${this.config.BASE_URL}${endpoint}`;

            for (let attempt = 0; attempt <= this.config.MAX_RETRIES; attempt++) {
                try {
                    const response = await this._fetchWithTimeout(url, options);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    return await response.json();
                } catch (error) {
                    lastError = error;
                    
                    if (error.name === 'AbortError') {
                        throw new Error('요청 시간이 초과되었습니다.');
                    }
                    
                    if (attempt < this.config.MAX_RETRIES) {
                        const delay = this.config.RETRY_DELAY * Math.pow(2, attempt);
                        await new Promise(resolve => setTimeout(resolve, delay));
                        continue;
                    }
                }
            }
            
            throw lastError;
        }

        // 타임아웃이 있는 fetch
        async _fetchWithTimeout(url, options = {}) {
            const controller = new AbortController();
            const timeout = setTimeout(() => {
                controller.abort();
            }, this.config.TIMEOUT);

            try {
                const headers = {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    ...securityManager.addSecurityHeaders(),
                    ...options.headers
                };

                // 인증 토큰이 있으면 헤더에 추가
                if (this.authToken) {
                    headers['Authorization'] = `Bearer ${this.authToken}`;
                }

                // CSRF 토큰 추가
                const csrfToken = securityManager.getCsrfToken();
                if (csrfToken) {
                    headers['X-CSRF-Token'] = csrfToken;
                }

                const response = await fetch(url, {
                    ...options,
                    headers,
                    signal: controller.signal,
                    credentials: 'include'  // 쿠키를 포함하여 요청
                });

                if (response.status === 401) {
                    // 인증 토큰이 만료되었거나 유효하지 않은 경우
                    this.clearAuthToken();
                    securityManager.logSecurityEvent({
                        type: 'UNAUTHORIZED_ACCESS',
                        details: '인증되지 않은 접근 시도'
                    });
                    
                    // 로그인 페이지로 리다이렉션하지 않고 오류만 발생
                    throw new Error('인증이 필요합니다. 다시 로그인해주세요.');
                }

                return response;
            } finally {
                clearTimeout(timeout);
            }
        }

        // GET 요청
        async get(endpoint, options = {}) {
            return this.request(endpoint, { ...options, method: 'GET' });
        }

        // POST 요청
        async post(endpoint, data, options = {}) {
            return this.request(endpoint, {
                ...options,
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        // PUT 요청
        async put(endpoint, data, options = {}) {
            return this.request(endpoint, {
                ...options,
                method: 'PUT',
                body: JSON.stringify(data)
            });
        }

        // DELETE 요청
        async delete(endpoint, options = {}) {
            return this.request(endpoint, { ...options, method: 'DELETE' });
        }
    }

    // API 클라이언트 인스턴스 생성
    const api = new ApiClient();

    // 이벤트 로그에 보안 처리 추가
    function addEventLog(event) {
        const eventList = document.querySelector('.div-22');
        const eventItem = document.createElement('div');
        eventItem.className = 'div-23';
        
        const icon = event.level === 'warning' ? 'warning' : 'error';
        const time = new Date(event.timestamp).toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });

        // XSS 방지를 위한 이스케이프 처리
        const sanitizedMessage = securityManager.sanitizeInput(event.message);
        const sanitizedCameraId = securityManager.sanitizeInput(event.camera_id);

        eventItem.innerHTML = `
            <i class="material-icons">${icon}</i>
            <div class="div-24">
                <div class="p">
                    <div class="text---------85c">
                        ${sanitizedMessage}
                    </div>
                </div>
                <div class="p-1">
                    <div class="text--2-114523">
                        카메라 ${sanitizedCameraId} - ${time}
                    </div>
                </div>
            </div>
        `;

        eventList.insertBefore(eventItem, eventList.firstChild);
        
        if (eventList.children.length > 10) {
            eventList.removeChild(eventList.lastChild);
        }
    }

    // 자동 로그아웃 타이머 보안 강화
    function updateAutoLogoutTimer(minutes) {
        if (autoLogoutTimer) {
            clearTimeout(autoLogoutTimer);
        }
        if (minutes > 0) {
            autoLogoutTimer = setTimeout(() => {
                securityManager.logSecurityEvent({
                    type: 'AUTO_LOGOUT',
                    details: '자동 로그아웃 실행'
                });
                showNotification('자동 로그아웃', '장시간 활동이 없어 자동으로 로그아웃됩니다.', 'warning');
                setTimeout(() => {
                    window.location.href = '/logout';
                }, 3000);
            }, minutes * 60 * 1000);
        }
    }

    // CSS 스타일 추가
    const style = document.createElement('style');
    style.textContent = `
        .logout-button {
            background: none;
            border: none;
            color: #fff;
            cursor: pointer;
            padding: 4px;
            margin-left: 8px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            transition: background-color 0.2s;
        }

        .logout-button:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }

        .logout-button i {
            font-size: 20px;
        }

        .security-lock-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }

        .lock-content {
            text-align: center;
        }

        .lock-content i {
            font-size: 48px;
            margin-bottom: 20px;
        }

        .lock-content h2 {
            margin-bottom: 10px;
        }
    `;
    document.head.appendChild(style);

    // 카메라 스트림 상태 관리
    const cameraStates = new Map();
    const MAX_STREAM_RETRIES = 3;
    const STREAM_RETRY_DELAY = 2000;

    // 기존의 fetchWithAuth 함수를 새로운 API 클라이언트로 교체
    async function updateCameraStreams() {
        try {
            const response = await api.get('/cameras');
            if (!Array.isArray(response)) {
                throw new Error('카메라 데이터 형식이 올바르지 않습니다. 관리자에게 문의하세요.');
            }
            
            if (response.length === 0) {
                console.warn('등록된 카메라가 없습니다.');
                return;
            }

            response.forEach(camera => {
                if (selectedCamera === 'all' || selectedCamera === camera.id.toString()) {
                    updateSingleCameraStream(camera);
                }
            });
        } catch (error) {
            console.error('카메라 스트림 업데이트 오류:', error);
            let errorMessage = '카메라 데이터를 불러오는 중 오류가 발생했습니다.';
            
            if (error.message.includes('카메라 데이터 형식이')) {
                errorMessage = error.message;
            } else if (error.message.includes('401')) {
                errorMessage = '인증이 만료되었습니다. 다시 로그인해주세요.';
            } else if (error.message.includes('404')) {
                errorMessage = '카메라 정보를 찾을 수 없습니다. 카메라가 올바르게 등록되어 있는지 확인해주세요.';
            } else if (error.message.includes('500')) {
                errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
            }
            
            showNotification('카메라 오류', errorMessage, 'error');
        }
    }

    // 단일 카메라 스트림 업데이트
    async function updateSingleCameraStream(camera) {
        const cameraContainer = document.querySelector(`.camera-container[data-camera-id="${camera.id}"]`);
        if (!cameraContainer) return;

        const streamImg = cameraContainer.querySelector('.camera-stream');
        const offlineDiv = cameraContainer.querySelector('.camera-offline');
        const loadingDiv = cameraContainer.querySelector('.camera-loading') || createLoadingElement(cameraContainer);

        // 현재 카메라 상태 가져오기
        const state = cameraStates.get(camera.id) || {
            retryCount: 0,
            lastSuccess: null,
            isLoading: false
        };

        if (state.isLoading) return; // 이미 로딩 중이면 중복 요청 방지

        try {
            state.isLoading = true;
            loadingDiv.style.display = 'flex';
            streamImg.style.display = 'none';
            offlineDiv.style.display = 'none';

            // 스트림 URL에 타임스탬프 추가하여 캐시 방지
            const timestamp = new Date().getTime();
            const streamUrl = `/api/v1/cameras/${camera.id}/stream?t=${timestamp}`;

            // 이미지 로드 프로미스
            await new Promise((resolve, reject) => {
                const tempImg = new Image();
                tempImg.onload = () => {
                    streamImg.src = streamUrl;
                    streamImg.style.display = 'block';
                    state.lastSuccess = Date.now();
                    state.retryCount = 0;
                    resolve();
                };
                tempImg.onerror = () => reject(new Error('스트림 로드 실패'));
                tempImg.src = streamUrl;

                // 5초 타임아웃 설정
                setTimeout(() => reject(new Error('스트림 로드 시간 초과')), 5000);
            });

        } catch (error) {
            console.error(`카메라 ${camera.id} 스트림 오류:`, error);
            state.retryCount++;

            if (state.retryCount <= MAX_STREAM_RETRIES) {
                // 재시도
                setTimeout(() => updateSingleCameraStream(camera), STREAM_RETRY_DELAY);
                showNotification('카메라 재연결', `카메라 ${camera.id} 재연결 시도 중... (${state.retryCount}/${MAX_STREAM_RETRIES})`, 'warning');
            } else {
                // 최대 재시도 횟수 초과
                streamImg.style.display = 'none';
                offlineDiv.style.display = 'flex';
                showNotification('카메라 오프라인', `카메라 ${camera.id}가 오프라인 상태입니다.`, 'error');
            }
        } finally {
            state.isLoading = false;
            loadingDiv.style.display = 'none';
            cameraStates.set(camera.id, state);
        }
    }

    // 로딩 표시 요소 생성
    function createLoadingElement(container) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'camera-loading';
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <span>카메라 로딩중...</span>
        `;
        container.appendChild(loadingDiv);
        return loadingDiv;
    }

    // 현재 시간 업데이트
    function updateClock() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const seconds = now.getSeconds();
        const ampm = hours < 12 ? "오전" : "오후";
        const displayHour = hours % 12 || 12;
        const timeString = ampm + " " +
            String(displayHour).padStart(2, '0') + ":" +
            String(minutes).padStart(2, '0') + ":" +
            String(seconds).padStart(2, '0');
        
        const clockElement = document.querySelector('.current-time .text--040931');
        if (clockElement) {
            clockElement.textContent = timeString;
        }
    }

    // 초기 시간 설정 및 1초마다 업데이트
    updateClock();
    setInterval(updateClock, 1000);

    // 전체화면 버튼 이벤트
    const fullscreenBtn = document.querySelector('.button-2');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        });
    }

    // 카메라 선택 이벤트
    const cameraSelect = document.querySelector('.select');
    if (cameraSelect) {
        cameraSelect.addEventListener('change', function(e) {
            selectedCamera = e.target.value;
            // 선택된 카메라 즉시 업데이트
            updateCameraStreams();
        });
    }

    // 이벤트 검색 기능
    const searchInput = document.querySelector('.input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const eventItems = document.querySelectorAll('.div-23, .div-25');
            
            eventItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // 설정 관리 클래스
    class SettingsManager {
        constructor(api) {
            this.api = api;
            this.settings = null;
            this.observers = new Set();
            this.validationRules = {
                sms_phone: {
                    validate: (value) => /^\d{10,11}$/.test(value),
                    message: '전화번호는 10-11자리의 숫자여야 합니다.'
                },
                violation_threshold: {
                    validate: (value) => value >= 1 && value <= 10,
                    message: '위반 임계값은 1에서 10 사이여야 합니다.'
                },
                auto_logout_time: {
                    validate: (value) => value >= 1 && value <= 120,
                    message: '자동 로그아웃 시간은 1분에서 120분 사이여야 합니다.'
                }
            };
        }

        // 설정 변경 감지를 위한 옵저버 등록
        addObserver(callback) {
            this.observers.add(callback);
        }

        // 옵저버 제거
        removeObserver(callback) {
            this.observers.delete(callback);
        }

        // 설정 변경 알림
        notifyObservers() {
            this.observers.forEach(callback => callback(this.settings));
        }

        // 설정 유효성 검사
        validateSettings(settings) {
            const errors = [];
            Object.entries(this.validationRules).forEach(([key, rule]) => {
                if (settings[key] !== undefined && !rule.validate(settings[key])) {
                    errors.push({ field: key, message: rule.message });
                }
            });
            return errors;
        }

        // 설정 로드
        async loadSettings() {
            try {
                const response = await this.api.get('/api/v1/settings');
                
                // 응답이 JSON이 아닌 경우 처리
                if (typeof response === 'string') {
                    try {
                        response = JSON.parse(response);
                    } catch (e) {
                        throw new Error('잘못된 응답 형식입니다.');
                    }
                }
                
                // 응답 구조 확인
                if (!response || typeof response !== 'object') {
                    throw new Error('설정 데이터를 받지 못했습니다.');
                }
                
                // 설정 데이터가 직접 응답에 있는 경우
                if (response.auto_logout_time !== undefined) {
                    this.settings = response;
                } 
                // 설정 데이터가 settings 객체 안에 있는 경우
                else if (response.settings) {
                    this.settings = response.settings;
                }
                // 그 외의 경우는 오류로 처리
                else {
                    throw new Error('설정 데이터 형식이 올바르지 않습니다.');
                }
                
                this.notifyObservers();
                return this.settings;
            } catch (error) {
                console.error('설정 로드 오류:', error);
                // 인증 오류인 경우 조용히 실패
                if (error.message.includes('인증이 필요합니다')) {
                    return null;
                }
                showNotification('설정 오류', '설정을 불러오는데 실패했습니다.', 'error');
                return null;
            }
        }

        // 설정 저장
        async saveSettings(newSettings) {
            try {
                const response = await this.api.post('/api/v1/settings', newSettings);
                if (response.ok) {
                    this.settings = { ...this.settings, ...newSettings };
                    this.notifyObservers();
                    showNotification('성공', '설정이 저장되었습니다.', 'success');
                    return true;
                } else {
                    throw new Error('설정 저장 실패');
                }
            } catch (error) {
                console.error('설정 저장 오류:', error);
                showNotification('오류', '설정을 저장하는 중 오류가 발생했습니다.', 'error');
                return false;
            }
        }

        // 특정 설정 값 가져오기
        getSetting(key) {
            return this.settings ? this.settings[key] : null;
        }

        // 설정 기본값으로 초기화
        async resetToDefaults() {
            try {
                await this.api.post('/settings/reset');
                await this.loadSettings();
                showNotification('설정 초기화', '설정이 기본값으로 초기화되었습니다.', 'info');
                return true;
            } catch (error) {
                console.error('설정 초기화 오류:', error);
                showNotification('설정 오류', '설정 초기화에 실패했습니다.', 'error');
                return false;
            }
        }
    }

    // 설정 매니저 인스턴스 생성
    const settingsManager = new SettingsManager(api);

    // 설정 폼 초기화
    function initSettingsForm() {
        const settingsForm = document.getElementById('settingsForm');
        const settingsModal = document.getElementById('settingsModal');
        if (!settingsForm) return;

        // 폼 제출 이벤트 처리
        settingsForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const settings = {
                auto_logout_time: parseInt(formData.get('auto_logout_time')),
                violation_threshold: parseInt(formData.get('violation_threshold')),
                notification_sound: formData.get('notification_sound') === 'on',
                ai_sensitivity: formData.get('ai_sensitivity'),
                auto_ai_enable: formData.get('auto_ai_enable') === 'on',
                person_detection: formData.get('person_detection') === 'on',
                helmet_detection: formData.get('helmet_detection') === 'on',
                ppe_detection: formData.get('ppe_detection') === 'on',
                danger_zone_detection: formData.get('danger_zone_detection') === 'on',
                sms_notification: formData.get('sms_notification') === 'on',
                email_notification: formData.get('email_notification') === 'on',
                sms_phone: formData.get('sms_phone') || ''
            };

            try {
                const response = await fetch('/api/v1/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...securityManager.addSecurityHeaders()
                    },
                    body: JSON.stringify(settings)
                });

                if (response.ok) {
                    showNotification('성공', '설정이 저장되었습니다.', 'success');
                    settingsModal.style.display = 'none';
                } else {
                    const data = await response.json();
                    throw new Error(data.message || '설정 저장에 실패했습니다.');
                }
            } catch (error) {
                console.error('설정 저장 오류:', error);
                showNotification('오류', error.message || '설정을 저장하는 중 오류가 발생했습니다.', 'error');
            }
        });

        // 취소 버튼 이벤트 처리
        const cancelButton = settingsForm.querySelector('.cancel-button');
        if (cancelButton) {
            cancelButton.addEventListener('click', function() {
                settingsModal.style.display = 'none';
            });
        }
    }

    // 설정 버튼과 모달 관련 요소들
    const settingsButton = document.querySelector('.settings-button');
    const settingsModal = document.getElementById('settingsModal');
    const closeButton = settingsModal.querySelector('.close-button');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    // 설정 버튼 클릭 이벤트
    settingsButton.addEventListener('click', () => {
        settingsModal.style.display = 'block';
    });

    // 닫기 버튼 클릭 이벤트
    closeButton.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });

    // 모달 외부 클릭시 닫기
    window.addEventListener('click', (event) => {
        if (event.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    // ESC 키로 모달 닫기
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && settingsModal.style.display === 'block') {
            settingsModal.style.display = 'none';
        }
    });

    // 탭 전환 기능
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // 활성 탭 버튼 변경
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // 탭 내용 변경
            const tabId = button.getAttribute('data-tab');
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });
        });
    });

    // 시스템 정보 업데이트 함수 업데이트
    async function updateSystemInfo() {
        try {
            const data = await api.get('/system/info');
            const memoryUsed = document.getElementById('memoryUsed');
            const memoryTotal = document.getElementById('memoryTotal');
            const progressBar = document.querySelector('.progress');
            
            if (memoryUsed && memoryTotal && progressBar) {
                memoryUsed.textContent = formatMemory(data.memory.used);
                memoryTotal.textContent = formatMemory(data.memory.total);
                const usagePercent = (data.memory.used / data.memory.total) * 100;
                progressBar.style.width = `${usagePercent}%`;
            }
        } catch (error) {
            console.error('시스템 정보 업데이트 오류:', error);
        }
    }
    
    // 메모리 크기 포맷 함수
    function formatMemory(bytes) {
        const gb = bytes / (1024 * 1024 * 1024);
        return `${gb.toFixed(1)} GB`;
    }

    // 초기화
    setupWebSocket();
    updateCameraStreams();
    // 5초마다 카메라 스트림 업데이트
    setInterval(updateCameraStreams, 5000);

    // 페이지 언로드시 웹소켓 연결 정리
    window.addEventListener('beforeunload', function() {
        if (ws) {
            ws.close();
        }
    });

    // 초기화
    initSettingsForm();

    // 직책 입력/수정 기능
    const positionDisplay = document.querySelector('.position-display');
    if (positionDisplay) {
        const positionText = positionDisplay.querySelector('.position-text');
        const editBtn = positionDisplay.querySelector('.edit-position-btn');
        const addBtn = positionDisplay.querySelector('.add-position-btn');
        const editContainer = positionDisplay.querySelector('.position-edit-container');
        const positionInput = positionDisplay.querySelector('.position-input');
        const saveBtn = positionDisplay.querySelector('.save-position-btn');
        const cancelBtn = positionDisplay.querySelector('.cancel-position-btn');
        
        // 입력/수정 버튼 클릭 이벤트
        function showEditForm() {
            positionText.style.display = 'none';
            if (editBtn) editBtn.style.display = 'none';
            if (addBtn) addBtn.style.display = 'none';
            editContainer.style.display = 'flex';
            positionInput.value = positionText.textContent === '미지정' ? '' : positionText.textContent;
            positionInput.focus();
        }
        
        if (editBtn) {
            editBtn.addEventListener('click', showEditForm);
        }
        
        if (addBtn) {
            addBtn.addEventListener('click', showEditForm);
        }
        
        // 저장 버튼 클릭 이벤트
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                const newPosition = positionInput.value.trim();
                try {
                    const response = await api.put('/api/v1/users/position', { 
                        position: newPosition,
                        csrf_token: securityManager.getCsrfToken()
                    });
                    const data = await response.json();
                    
                    if (data && data.success) {
                        positionText.textContent = newPosition || '미지정';
                        editContainer.style.display = 'none';
                        positionText.style.display = 'inline';
                        
                        if (newPosition) {
                            if (addBtn) addBtn.style.display = 'none';
                            if (editBtn) editBtn.style.display = 'inline';
                        } else {
                            if (editBtn) editBtn.style.display = 'none';
                            if (addBtn) addBtn.style.display = 'inline';
                        }
                        
                        showNotification('직책 변경', '직책이 성공적으로 변경되었습니다.', 'info');
                    } else {
                        throw new Error(data?.message || '직책 변경에 실패했습니다.');
                    }
                } catch (error) {
                    console.error('직책 변경 오류:', error);
                    if (error.message.includes('405')) {
                        showNotification('오류', 'API 메서드가 올바르지 않습니다. 관리자에게 문의하세요.', 'error');
                    } else {
                        showNotification('오류', error.message || '직책 변경에 실패했습니다.', 'error');
                    }
                }
            });
        }
        
        // 취소 버튼 클릭 이벤트
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                editContainer.style.display = 'none';
                positionText.style.display = 'inline';
                if (editBtn) editBtn.style.display = 'inline';
                if (addBtn) addBtn.style.display = 'inline';
                positionInput.value = positionText.textContent === '미지정' ? '' : positionText.textContent;
            });
        }
    }

    // 로그인 성공 후 처리
    async function handleLoginSuccess(token, remember = false) {
        api.setAuthToken(token, remember);
        const redirectPath = sessionStorage.getItem('redirectAfterLogin') || '/';
        sessionStorage.removeItem('redirectAfterLogin');
        window.location.href = redirectPath;
    }

    // 로그인 폼 이벤트 리스너
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const remember = formData.get('remember') === 'on';

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...securityManager.addSecurityHeaders()
                    },
                    body: JSON.stringify({
                        username: formData.get('username'),
                        password: formData.get('password')
                    })
                });

                const data = await response.json();
                if (response.ok && data.token) {
                    await handleLoginSuccess(data.token, remember);
                } else {
                    throw new Error(data.message || '로그인에 실패했습니다.');
                }
            } catch (error) {
                console.error('로그인 오류:', error);
                showNotification('로그인 실패', error.message, 'error');
            }
        });
    }

    // 아바타 선택 기능
    const avatarOptions = document.querySelectorAll('.avatar-option');
    const userAvatar = document.querySelector('.img-1');
    
    // 현재 선택된 아바타 표시
    const currentAvatar = userAvatar.style.backgroundImage;
    avatarOptions.forEach(option => {
        const avatarImg = option.querySelector('img').src;
        if (currentAvatar.includes(avatarImg)) {
            option.classList.add('selected');
        }
        
        // 아바타 선택 이벤트
        option.addEventListener('click', function() {
            const avatarId = this.dataset.avatar;
            
            // 선택 표시 업데이트
            avatarOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            
            // 아바타 이미지 업데이트
            userAvatar.style.backgroundImage = `url('/static/images/avatar_${avatarId}.png')`;
            
            // 선택된 아바타 저장 (로컬 스토리지)
            localStorage.setItem('selectedAvatar', avatarId);
            
            // TODO: 서버에 선택된 아바타 저장 (필요한 경우)
        });
    });
}); 