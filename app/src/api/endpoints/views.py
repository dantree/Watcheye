
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ...services.auth import get_current_user
from ...models.database import get_db

router = APIRouter(prefix="", tags=["views"])

@router.get("/", response_class=HTMLResponse)
async def view_page(request: Request, db: Session = Depends(get_db)):
    # 쿠키에서 access_token 읽기
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # 토큰과 DB 세션을 이용해 현재 사용자를 조회합니다.
        current_user = await get_current_user(token=token, db=db)
        html_content = """
        <html>
            <head>
                <title>지켜봄 - 모니터링</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    /* 공통 스타일 */
                    body {
                        margin: 0;
                        padding: 0;
                        font-family: 'Noto Sans KR', sans-serif;
                        background: #f5f5f5;
                    }

                    /* 모달 스타일 */
                    .modal {
                        display: none;
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0, 0, 0, 0.5);
                        z-index: 1000;
                    }

                    .modal-content {
                        position: relative;
                        background: white;
                        margin: 40px auto;
                        padding: 0;
                        border-radius: 12px;
                        max-width: 800px;
                        width: 90%;
                        max-height: 90vh;
                        overflow-y: auto;
                    }

                    .modal-content.wide {
                        max-width: 1200px;
                    }

                    .modal-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 16px 24px;
                        border-bottom: 1px solid #e0e0e0;
                    }

                    .modal-body {
                        padding: 24px;
                    }

                    /* 모니터링 스타일 */
                    .monitoring-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                        margin-bottom: 24px;
                    }

                    .monitor-card {
                        background: white;
                        padding: 20px;
                        border-radius: 12px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }

                    .monitor-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 16px;
                    }

                    .monitor-value {
                        font-size: 18px;
                        font-weight: 500;
                        color: #1a73e8;
                    }

                    .progress-bar {
                        height: 8px;
                        background: #f1f3f4;
                        border-radius: 4px;
                        overflow: hidden;
                        margin-bottom: 16px;
                    }

                    .progress {
                        height: 100%;
                        background: #1a73e8;
                        transition: width 0.3s ease;
                    }

                    .progress.warning {
                        background: #fbbc05;
                    }

                    .progress.danger {
                        background: #ea4335;
                    }

                    /* 시스템 로그 스타일 */
                    .system-logs {
                        background: white;
                        padding: 20px;
                        border-radius: 12px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        margin-top: 24px;
                    }

                    .log-viewer {
                        height: 200px;
                        overflow-y: auto;
                        background: #f8f9fa;
                        padding: 12px;
                        border-radius: 4px;
                        font-family: monospace;
                        font-size: 14px;
                    }

                    .log-item {
                        margin-bottom: 4px;
                        padding: 4px 8px;
                        border-radius: 4px;
                    }

                    .log-item.info {
                        background: #e8f0fe;
                        color: #1a73e8;
                    }

                    .log-item.warning {
                        background: #fef7e0;
                        color: #f9ab00;
                    }

                    .log-item.error {
                        background: #fce8e6;
                        color: #d93025;
                    }

                    .top-bar {
                        background: white;
                        padding: 12px 24px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        margin-bottom: 24px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }

                    .menu-button {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        background: #1a73e8;
                        color: white;
                        cursor: pointer;
                        font-size: 14px;
                        transition: background 0.3s;
                    }

                    .menu-button span {
                        display: inline;  /* 기본적으로 텍스트 표시 */
                    }

                    /* 반응형 스타일 */
                    @media (max-width: 1024px) {
                        .menu-button {
                            padding: 8px;  /* 패딩 축소 */
                        }
                        
                        .menu-button span {
                            display: none;  /* 텍스트 숨김 */
                        }
                        
                        .menu-button i {
                            margin: 0;  /* 아이콘 마진 제거 */
                        }

                        .logo span {
                            display: none;  /* 로고 텍스트 숨김 */
                        }
                    }

                    @media (max-width: 768px) {
                        .top-bar {
                            padding: 12px;
                        }
                        
                        .menu-items, .user-menu {
                            gap: 8px;  /* 버튼 간격 축소 */
                        }
                        
                        .menu-button {
                            padding: 6px;  /* 패딩 더 축소 */
                        }
                    }

                    .logo {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 20px;
                        font-weight: 500;
                        color: #1a73e8;
                    }

                    .logo i {
                        font-size: 24px;
                    }

                    .menu-items {
                        display: flex;
                        gap: 16px;
                    }

                    .user-menu {
                        display: flex;
                        gap: 16px;
                    }

                    # .menu-button {
                    #     display: flex;
                    #     align-items: center;
                    #     gap: 8px;
                    #     padding: 8px 16px;
                    #     border: none;
                    #     border-radius: 4px;
                    #     background: #1a73e8;
                    #     color: white;
                    #     cursor: pointer;
                    #     font-size: 14px;
                    #     transition: background 0.3s;
                    # }

                    .menu-button:hover {
                        background: #1557b0;
                    }

                    .menu-button.danger {
                        background: #dc3545;
                    }

                    .menu-button.danger:hover {
                        background: #c82333;
                    }

                    .menu-button i {
                        font-size: 20px;
                    }

                    .main-content {
                        padding: 0 24px 24px;
                    }

                    .status-bar {
                        background: white;
                        padding: 12px 24px;
                        border-radius: 8px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 24px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }

                    .status-item {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        color: #5f6368;
                    }

                    .status-item i {
                        color: #4CAF50;
                    }

                    .time-display {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        color: #1a73e8;
                    }

                    .camera-grid {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);  /* 기본 2열 */
                        gap: 24px;
                        margin-bottom: 24px;
                    }

                    /* 반응형 스타일 */
                    @media (max-width: 1024px) {  /* 태블릿 크기에서 1열로 변경 */
                        .camera-grid {
                            grid-template-columns: 1fr;  /* 1열로 변경 */
                        }
                        
                        .camera-cell {
                            max-width: 100%;  /* 너비 제한 해제 */
                        }
                    }

                    @media (max-width: 768px) {  /* 모바일 대응 */
                        .main-content {
                            padding: 0 12px 12px;
                        }
                        
                        .camera-grid {
                            gap: 16px;  /* 간격 줄임 */
                        }
                        
                        .camera-header {
                            padding: 8px;
                        }
                        
                        .camera-footer {
                            padding: 8px;
                        }
                    }

                    .camera-cell {
                        background: white;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }

                    .camera-header {
                        padding: 12px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        border-bottom: 1px solid #e0e0e0;
                    }

                    .camera-controls {
                        display: flex;
                        gap: 8px;
                    }

                    .control-button {
                        background: none;
                        border: none;
                        padding: 4px;
                        cursor: pointer;
                        color: #5f6368;
                        border-radius: 4px;
                        transition: all 0.3s ease;
                    }

                    .control-button:hover {
                        background: #f1f3f4;
                    }

                    .control-button.active {
                        background: #f1f3f4;
                    }

                    .control-button.active i {
                        color: #1a73e8;
                    }

                    .camera-feed {
                        position: relative;
                        aspect-ratio: 16/9;
                        background: #000;
                    }

                    .camera-feed img {
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                    }

                    .no-signal {
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        color: #fff;
                    }

                    .camera-footer {
                        padding: 12px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        border-top: 1px solid #e0e0e0;
                    }

                    .status-icon {
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #ea4335;
                    }

                    .status-icon.connected {
                        background: #4CAF50;
                    }

                    .alert-banner {
                        position: fixed;
                        top: 20px;
                        left: 50%;
                        transform: translateX(-50%);
                        padding: 12px 24px;
                        border-radius: 8px;
                        background: white;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        display: none;
                        z-index: 1000;
                    }

                    .alert-banner.show {
                        display: block;
                    }

                    .alert-banner.success {
                        background: #4CAF50;
                        color: white;
                    }

                    .alert-banner.error {
                        background: #f44336;
                        color: white;
                    }

                    .alert-banner.info {
                        background: #2196F3;
                        color: white;
                    }

                    /* 전체화면 모드 */
                    .camera-cell.active {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        z-index: 1000;
                        background: #000;
                    }

                    .camera-cell.active .camera-feed {
                        height: calc(100% - 100px);
                    }
                    /* 로그 스타일 */
                    .log-entry {
                        padding: 4px 8px;
                        border-left: 3px solid transparent;
                        margin-bottom: 4px;
                    }

                    .log-entry.info {
                        border-left-color: #2196F3;
                    }

                    .log-entry.warning {
                        border-left-color: #FFC107;
                    }

                    .log-entry.error {
                        border-left-color: #F44336;
                    }

                    .log-time {
                        color: #888;
                        margin-right: 8px;
                    }

                    .log-container::-webkit-scrollbar {
                        width: 8px;
                    }

                    .log-container::-webkit-scrollbar-track {
                        background: #2e2e2e;
                    }

                    .log-container::-webkit-scrollbar-thumb {
                        background: #666;
                        border-radius: 4px;
                    }
                </style>
            </head>
            <body>
                <!-- 상단 메뉴바 추가 -->
                <div class="top-bar">
                    <div class="logo">
                        <i class="material-icons">visibility</i>
                        <span>지켜봄</span>
                    </div>
                    <div class="menu-items">
                        <button onclick="openDashboard()" class="menu-button">
                            <i class="material-icons">dashboard</i>
                            <span>대시보드<span/>
                        </button>
                        <button onclick="openMonitoring()" class="menu-button">
                            <i class="material-icons">monitor</i>
                            <span>시스템 모니터링<span/>
                        </button>
                        <button onclick="openCameraSettings()" class="menu-button">
                            <i class="material-icons">videocam</i>
                            <span>카메라 설정<span/>
                        </button>
                        <button onclick="openSettings()" class="menu-button">
                            <i class="material-icons">settings</i>
                            <span>설정<span/>
                        </button>
                    </div>
                    <div class="user-menu">
                        <button onclick="openUserManagement()" class="menu-button">
                            <i class="material-icons">people</i>
                            <span>사용자 관리<span/>
                        </button>
                        <button onclick="logout()" class="menu-button danger">
                            <i class="material-icons">logout</i>
                            <span>로그아웃<span/>
                        </button>
                    </div>
                </div>

                <!-- 모니터링 모달 -->
                <div class="modal" id="monitoring-modal">
                    <div class="modal-content wide">
                        <div class="modal-header">
                            <h2>시스템 모니터링</h2>
                            <button class="close-button" onclick="closeMonitoring()">
                                <i class="material-icons">close</i>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="monitoring-grid">
                                <!-- CPU 사용량 -->
                                <div class="monitor-card">
                                    <div class="monitor-header">
                                        <h3>CPU 사용량</h3>
                                        <span class="monitor-value" id="cpu-usage">0%</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress" id="cpu-progress" style="width: 0%"></div>
                                    </div>
                                    <div class="monitor-details">
                                        <div class="detail-item">
                                            <span>코어 수</span>
                                            <span id="cpu-cores">0</span>
                                        </div>
                                        <div class="detail-item">
                                            <span>프로세스</span>
                                            <span id="process-count">0</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- 메모리 사용량 -->
                                <div class="monitor-card">
                                    <div class="monitor-header">
                                        <h3>메모리 사용량</h3>
                                        <span class="monitor-value" id="memory-usage">0GB / 0GB</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress" id="memory-progress" style="width: 0%"></div>
                                    </div>
                                    <div class="monitor-details">
                                        <div class="detail-item">
                                            <span>사용 중</span>
                                            <span id="memory-used">0GB</span>
                                        </div>
                                        <div class="detail-item">
                                            <span>여유</span>
                                            <span id="memory-free">0GB</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- 디스크 사용량 -->
                                <div class="monitor-card">
                                    <div class="monitor-header">
                                        <h3>디스크 사용량</h3>
                                        <span class="monitor-value" id="disk-usage">0GB / 0GB</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress" id="disk-progress" style="width: 0%"></div>
                                    </div>
                                    <div class="monitor-details">
                                        <div class="detail-item">
                                            <span>사용 중</span>
                                            <span id="disk-used">0GB</span>
                                        </div>
                                        <div class="detail-item">
                                            <span>여유</span>
                                            <span id="disk-free">0GB</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- GPU 사용량 -->
                                <div class="monitor-card">
                                    <div class="monitor-header">
                                        <h3>GPU 사용량</h3>
                                        <span class="monitor-value" id="gpu-usage">0%</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress" id="gpu-progress" style="width: 0%"></div>
                                    </div>
                                    <div class="monitor-details">
                                        <div class="detail-item">
                                            <span>메모리</span>
                                            <span id="gpu-memory">0GB / 0GB</span>
                                        </div>
                                        <div class="detail-item">
                                            <span>온도</span>
                                            <span id="gpu-temp">0°C</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 시스템 로그 -->
                            <div class="system-logs">
                                <h3>시스템 로그</h3>
                                <div class="log-viewer" id="system-log-viewer">
                                    <!-- 로그 항목들이 여기에 동적으로 추가됨 -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 메인 컨텐츠 영역 -->
                <div class="main-content">
                    <!-- 상태 표시줄 -->
                    <div class="status-bar">
                        <div class="status-item">
                            <i class="material-icons">network_check</i>
                            <span id="network-status">연결됨</span>
                        </div>
                        <div class="status-item">
                            <i class="material-icons">memory</i>
                            <span id="ai-status">AI 활성화</span>
                        </div>
                        <div class="time-display">
                            <i class="material-icons">schedule</i>
                            <span id="current-time">00:00:00</span>
                        </div>
                    </div>

                    <!-- 카메라 그리드 -->
                    <div class="camera-grid">
                        <!-- 카메라 1 -->
                        <div class="camera-cell" id="camera-0">
                            <div class="camera-header">
                                <span class="camera-name">카메라 1</span>
                                <div class="camera-controls">
                                    <button onclick="toggleCamera(0)" class="control-button">
                                        <i class="material-icons">power_settings_new</i>
                                    </button>
                                    <button onclick="toggleAI(0)" class="control-button">
                                        <i class="material-icons">psychology</i>
                                    </button>
                                    <button onclick="toggleFullscreen(0)" class="control-button">
                                        <i class="material-icons">fullscreen</i>
                                    </button>
                                </div>
                            </div>
                            <div class="camera-feed">
                                <img src="" alt="Camera 1">
                                <div class="no-signal">
                                    <i class="material-icons">videocam_off</i>
                                    <span>신호 없음</span>
                                </div>
                            </div>
                            <div class="camera-footer">
                                <div class="status-icon"></div>
                                <span class="fps" id="fps-0">0 FPS</span>
                            </div>
                        </div>

                        <!-- 카메라 2 -->
                        <div class="camera-cell" id="camera-1">
                            <div class="camera-header">
                                <span class="camera-name">카메라 2</span>
                                <div class="camera-controls">
                                    <button onclick="toggleCamera(1)" class="control-button">
                                        <i class="material-icons">power_settings_new</i>
                                    </button>
                                    <button onclick="toggleAI(1)" class="control-button">
                                        <i class="material-icons">psychology</i>
                                    </button>
                                    <button onclick="toggleFullscreen(1)" class="control-button">
                                        <i class="material-icons">fullscreen</i>
                                    </button>
                                </div>
                            </div>
                            <div class="camera-feed">
                                <img src="" alt="Camera 2">
                                <div class="no-signal">
                                    <i class="material-icons">videocam_off</i>
                                    <span>신호 없음</span>
                                </div>
                            </div>
                            <div class="camera-footer">
                                <div class="status-icon"></div>
                                <span class="fps" id="fps-1">0 FPS</span>
                            </div>
                        </div>

                        <!-- 카메라 3 -> 로그 뷰어로 변경 -->
                        <div class="camera-cell" id="camera-3">
                            <div class="camera-header">
                                <span class="camera-name">시스템 로그</span>
                                <div class="camera-controls">
                                    <button onclick="clearLogs()" class="control-button">
                                        <i class="material-icons">clear_all</i>
                                    </button>
                                    <button onclick="toggleAutoScroll()" class="control-button">
                                        <i class="material-icons">vertical_align_bottom</i>
                                    </button>
                                    <button onclick="toggleFullscreen(3)" class="control-button">
                                        <i class="material-icons">fullscreen</i>
                                    </button>
                                </div>
                            </div>
                            <div class="log-container" style="height: 100%; overflow-y: auto; background: #1e1e1e; padding: 12px;">
                                <div id="log-content" style="font-family: monospace; font-size: 12px; color: #fff;">
                                    <!-- 로그 내용이 여기에 추가됨 -->
                                </div>
                            </div>
                        </div>

                        <!-- 카메라 4 -->
                        <div class="camera-cell" id="camera-3">
                            <div class="camera-header">
                                <span class="camera-name">카메라 4</span>
                                <div class="camera-controls">
                                    <button onclick="toggleCamera(3)" class="control-button">
                                        <i class="material-icons">power_settings_new</i>
                                    </button>
                                    <button onclick="toggleAI(3)" class="control-button">
                                        <i class="material-icons">psychology</i>
                                    </button>
                                    <button onclick="toggleFullscreen(3)" class="control-button">
                                        <i class="material-icons">fullscreen</i>
                                    </button>
                                </div>
                            </div>
                            <div class="camera-feed">
                                <img src="" alt="Camera 4">
                                <div class="no-signal">
                                    <i class="material-icons">videocam_off</i>
                                    <span>신호 없음</span>
                                </div>
                            </div>
                            <div class="camera-footer">
                                <div class="status-icon"></div>
                                <span class="fps" id="fps-3">0 FPS</span>
                            </div>
                        </div>
                    </div>

                    <!-- 알림 배너 -->
                    <div class="alert-banner" id="alert-banner"></div>
                </div>

                <script>
                    // 모니터링 관련 변수
                    let monitoringInterval = null;

                    // 모니터링 모달 열기/닫기
                    function openMonitoring() {
                        openModal('monitoring-modal');
                        startMonitoring();
                    }

                    function closeMonitoring() {
                        closeModal('monitoring-modal');
                        stopMonitoring();
                    }

                    // 모니터링 시작/중지
                    function startMonitoring() {
                        updateSystemStatus();
                        monitoringInterval = setInterval(updateSystemStatus, 3000);  // 3초마다 업데이트
                    }

                    function stopMonitoring() {
                        if (monitoringInterval) {
                            clearInterval(monitoringInterval);
                            monitoringInterval = null;
                        }
                    }

                    // 시스템 상태 업데이트
                    async function updateSystemStatus() {
                        try {
                            const response = await fetch('/api/v1/system/status');
                            const data = await response.json();
                            
                            if (data.success) {
                                updateCpuStatus(data.cpu);
                                updateMemoryStatus(data.memory);
                                updateDiskStatus(data.disk);
                                updateGpuStatus(data.gpu);
                                updateSystemLogs(data.logs);
                            }
                        } catch (error) {
                            console.error('시스템 상태 업데이트 실패:', error);
                        }
                    }

                    // 각 컴포넌트 상태 업데이트 함수들
                    function updateCpuStatus(cpu) {
                        document.getElementById('cpu-usage').textContent = `${cpu.usage}%`;
                        document.getElementById('cpu-cores').textContent = cpu.cores;
                        document.getElementById('process-count').textContent = cpu.processes;
                        updateProgressBar('cpu-progress', cpu.usage);
                    }

                    function updateMemoryStatus(memory) {
                        const totalGB = formatGB(memory.total);
                        const usedGB = formatGB(memory.used);
                        const freeGB = formatGB(memory.free);
                        
                        document.getElementById('memory-usage').textContent = `${usedGB}GB / ${totalGB}GB`;
                        document.getElementById('memory-used').textContent = `${usedGB}GB`;
                        document.getElementById('memory-free').textContent = `${freeGB}GB`;
                        
                        const usagePercent = (memory.used / memory.total * 100).toFixed(1);
                        updateProgressBar('memory-progress', usagePercent);
                    }

                    function updateDiskStatus(disk) {
                        const totalGB = formatGB(disk.total);
                        const usedGB = formatGB(disk.used);
                        const freeGB = formatGB(disk.free);
                        
                        document.getElementById('disk-usage').textContent = `${usedGB}GB / ${totalGB}GB`;
                        document.getElementById('disk-used').textContent = `${usedGB}GB`;
                        document.getElementById('disk-free').textContent = `${freeGB}GB`;
                        
                        const usagePercent = (disk.used / disk.total * 100).toFixed(1);
                        updateProgressBar('disk-progress', usagePercent);
                    }

                    function updateGpuStatus(gpu) {
                        document.getElementById('gpu-usage').textContent = `${gpu.usage}%`;
                        document.getElementById('gpu-memory').textContent = 
                            `${gpu.memory_used}GB / ${gpu.memory_total}GB`;
                        document.getElementById('gpu-temp').textContent = `${gpu.temperature}°C`;
                        updateProgressBar('gpu-progress', gpu.usage);
                    }

                    // 유틸리티 함수들
                    function formatGB(bytes) {
                        return (bytes / 1024 / 1024 / 1024).toFixed(1);
                    }

                    function updateProgressBar(elementId, value) {
                        const progress = document.getElementById(elementId);
                        progress.style.width = `${value}%`;
                        
                        if (value > 90) {
                            progress.className = 'progress danger';
                        } else if (value > 70) {
                            progress.className = 'progress warning';
                        } else {
                            progress.className = 'progress';
                        }
                    }

                    // 시스템 로그 업데이트
                    function updateSystemLogs(logs) {
                        const logViewer = document.getElementById('system-log-viewer');
                        const recentLogs = logs.slice(-50);  // 최근 50개만 표시
                        
                        logViewer.innerHTML = recentLogs.map(log => `
                            <div class="log-item ${log.level.toLowerCase()}">
                                <span class="log-time">[${formatDateTime(log.timestamp)}]</span>
                                <span class="log-message">${log.message}</span>
                            </div>
                        `).join('');
                        
                        logViewer.scrollTop = logViewer.scrollHeight;  // 자동 스크롤
                    }

                    // 모달 제어 함수
                    function openModal(modalId) {
                        document.getElementById(modalId).style.display = 'block';
                    }

                    function closeModal(modalId) {
                        document.getElementById(modalId).style.display = 'none';
                    }

                    // 날짜/시간 포맷 함수
                    function formatDateTime(isoString) {
                        const date = new Date(isoString);
                        return date.toLocaleString('ko-KR');
                    }

                    // 메뉴 관련 함수들
                    function openDashboard() {
                        openModal('dashboard-modal');
                    }

                    function openCameraSettings() {
                        openModal('camera-settings-modal');
                    }

                    function openSettings() {
                        openModal('settings-modal');
                    }

                    function openUserManagement() {
                        openModal('users-modal');
                    }

                    function logout() {
                        if (confirm('로그아웃 하시겠습니까?')) {
                            // POST 방식으로 로그아웃을 호출하는 예시:
                            fetch('/api/auth/logout', {
                                method: 'POST',
                                credentials: 'same-origin'
                            })
                            .then(response => {
                                // 로그아웃 성공 시 리다이렉트된 페이지로 이동합니다.
                                if (response.redirected) {
                                    window.location.href = response.url;
                                } else {
                                    window.location.href = '/login';
                                }
                            })
                            .catch(error => {
                                console.error('로그아웃 실패:', error);
                                alert('로그아웃 중 오류가 발생했습니다.');
                            });
                        }
                    }


                    // FPS 계산을 위한 변수들
                    const fpsCounters = new Map();  // 각 카메라별 FPS 카운터

                    // FPS 계산 함수
                    function initFPSCounter(cameraId) {
                        fpsCounters.set(cameraId, {
                            frameCount: 0,
                            lastTime: performance.now(),
                            fps: 0
                        });
                    }

                    function updateFPS(cameraId) {
                        const counter = fpsCounters.get(cameraId);
                        if (!counter) return;

                        counter.frameCount++;
                        const now = performance.now();
                        const elapsed = now - counter.lastTime;

                        if (elapsed >= 1000) {  // 1초마다 FPS 업데이트
                            counter.fps = Math.round((counter.frameCount * 1000) / elapsed);
                            counter.frameCount = 0;
                            counter.lastTime = now;

                            // FPS 표시 업데이트
                            const fpsElement = document.getElementById(`fps-${cameraId}`);
                            if (fpsElement) {
                                fpsElement.textContent = `${counter.fps} FPS`;
                            }
                        }
                    }

                    // 웹캠 스트림 시작 함수 수정
                    function startWebcamStream(cameraId) {
                        const img = document.querySelector(`#camera-${cameraId} img`);
                        initFPSCounter(cameraId);  // FPS 카운터 초기화

                        img.onload = () => {
                            updateFPS(cameraId);  // 프레임이 로드될 때마다 FPS 업데이트
                            // 다음 프레임 요청
                            img.src = `/api/v1/cameras/${cameraId}/stream?t=${Date.now()}`;
                        };

                        img.onerror = () => {
                            // 오류 발생 시 잠시 후 다시 시도
                            setTimeout(() => {
                                img.src = `/api/v1/cameras/${cameraId}/stream?t=${Date.now()}`;
                            }, 1000);
                        };

                        // 첫 프레임 요청
                        img.src = `/api/v1/cameras/${cameraId}/stream`;
                    }

                    // 카메라 관련 변수
                    let startTime = performance.now();
                    let frameCount = 0;
                    let activeStreams = new Set();
                    let activeCameraCell = null;

                    // 시계 업데이트
                    function updateClock() {
                        const now = new Date();
                        document.getElementById('current-time').textContent = 
                            now.toLocaleString('ko-KR');
                    }

                    // 웹캠 초기화
                    function initWebcam(cameraId) {
                        const cameraCell = document.getElementById(`camera-${cameraId}`);
                        const img = cameraCell.querySelector('img');
                        const noSignal = cameraCell.querySelector('.no-signal');
                        const statusIcon = cameraCell.querySelector('.status-icon');
                        
                        try {
                            fetch('/api/v1/init-webcam', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ camera_id: cameraId })
                            }).then(response => {
                                if (response.ok) {
                                    img.style.display = 'block';
                                    img.src = `/api/v1/cameras/${cameraId}/stream`;
                                    noSignal.style.display = 'none';
                                    statusIcon.classList.add('connected');
                                    activeStreams.add(cameraId);
                                    
                                    // FPS 계산 시작
                                    img.onload = () => calculateFPS(cameraId);
                                }
                            });
                        } catch (error) {
                            console.error('Error:', error);
                            statusIcon.classList.add('error');
                        }
                    }

                    // 전체화면 토글
                    function toggleFullscreen(cameraId) {
                        const cameraCell = document.getElementById(`camera-${cameraId}`);
                        
                        if (activeCameraCell === cameraCell) {
                            cameraCell.classList.remove('active');
                            activeCameraCell = null;
                        } else {
                            if (activeCameraCell) {
                                activeCameraCell.classList.remove('active');
                            }
                            cameraCell.classList.add('active');
                            activeCameraCell = cameraCell;
                        }
                    }

                    // 카메라 ON/OFF 토글
                    async function toggleCamera(cameraId) {
                        try {
                            const cameraCell = document.getElementById(`camera-${cameraId}`);
                            const powerButton = cameraCell.querySelector('.control-button[onclick^="toggleCamera"]');
                            const powerIcon = powerButton.querySelector('i');
                            const statusIcon = cameraCell.querySelector('.status-icon');
                            const img = cameraCell.querySelector('img');
                            const noSignal = cameraCell.querySelector('.no-signal');

                            const response = await fetch(`/api/v1/cameras/${cameraId}/toggle`, {
                                method: 'POST'
                            });
                            const data = await response.json();
                            
                            if (data.status === 'on') {
                                // 카메라 켜짐 상태
                                powerButton.classList.add('active');
                                powerIcon.style.color = '#4CAF50';
                                statusIcon.classList.add('connected');
                                img.style.display = 'block';
                                noSignal.style.display = 'none';
                                startWebcamStream(cameraId);
                                initFPSCounter(cameraId);  // FPS 카운터 초기화
                            } else {
                                // 카메라 꺼짐 상태
                                powerButton.classList.remove('active');
                                powerIcon.style.color = '#5f6368';
                                statusIcon.classList.remove('connected');
                                img.style.display = 'none';
                                noSignal.style.display = 'flex';
                                document.getElementById(`fps-${cameraId}`).textContent = '0 FPS';  // FPS 초기화
                            }
                        } catch (error) {
                            console.error('Error:', error);
                            showAlert('카메라 제어 중 오류가 발생했습니다.', 'error');
                        }
                    }


                    // AI 토글
                    async function toggleAI(cameraId) {
                        try {
                            const cameraCell = document.getElementById(`camera-${cameraId}`);
                            const aiButton = cameraCell.querySelector('.control-button[onclick^="toggleAI"]');
                            const aiIcon = aiButton.querySelector('i');

                            const enabled = !aiButton.classList.contains('active');
                            const response = await fetch(`/api/v1/cameras/${cameraId}/ai`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ enabled: enabled })
                            });

                            if (response.ok) {
                                const data = await response.json();
                                if (data.success) {
                                    if (enabled) {
                                        aiButton.classList.add('active');
                                        aiIcon.style.color = '#1a73e8';  // 파란색
                                        showAlert('AI 감지가 활성화되었습니다.', 'success');
                                    } else {
                                        aiButton.classList.remove('active');
                                        aiIcon.style.color = '#5f6368';  // 회색
                                        showAlert('AI 감지가 비활성화되었습니다.', 'info');
                                    }
                                }
                            } else {
                                throw new Error('AI 제어 실패');
                            }
                        } catch (error) {
                            console.error('Error:', error);
                            showAlert('AI 제어 중 오류가 발생했습니다.', 'error');
                        }
                    }

                    // 알림 표시 함수
                    function showAlert(message, type = 'info') {
                        const alertBanner = document.getElementById('alert-banner');
                        alertBanner.textContent = message;
                        alertBanner.className = `alert-banner show ${type}`;
                        
                        setTimeout(() => {
                            alertBanner.classList.remove('show');
                        }, 3000);
                    }

                    // 1초마다 시계 업데이트
                    setInterval(updateClock, 1000);
                    updateClock();

                    // 페이지 로드 시 카메라 초기화
                    document.addEventListener('DOMContentLoaded', async () => {
                        // 웹캠 초기화
                        try {
                            const response = await fetch('/api/v1/init-webcam', {
                                method: 'POST'
                            });
                            if (response.ok) {
                                // 웹캠 스트림 시작
                                //startWebcamStream(0);
                                document.querySelector('#camera-0 .status-icon').classList.add('connected');
                            }
                        } catch (error) {
                            console.error('웹캠 초기화 실패:', error);
                        }

                        // 나머지 카메라 초기화
                        for (let i = 1; i <= 3; i++) {
                            initWebcam(i);
                        }

                        // 모달 이벤트 리스너
                        document.getElementById('monitoring-modal').addEventListener('hidden', stopMonitoring);
                    });

                    //로그 기능
                    let autoScroll = true;
                    let logs = [];

                    function addLog(message, level = 'info') {
                        const now = new Date();
                        const logEntry = {
                            timestamp: now.toISOString(),
                            message: message,
                            level: level
                        };
                        
                        logs.push(logEntry);
                        updateLogDisplay();
                    }

                    function updateLogDisplay() {
                        const logContent = document.getElementById('log-content');
                        logContent.innerHTML = logs.map(log => `
                            <div class="log-entry ${log.level}">
                                <span class="log-time">[${formatDateTime(log.timestamp)}]</span>
                                <span class="log-message">${log.message}</span>
                            </div>
                        `).join('');
                        
                        if (autoScroll) {
                            logContent.scrollTop = logContent.scrollHeight;
                        }
                    }

                    function clearLogs() {
                        logs = [];
                        updateLogDisplay();
                    }

                    function toggleAutoScroll() {
                        autoScroll = !autoScroll;
                        const scrollButton = document.querySelector('#camera-3 .camera-controls button:nth-child(2)');
                        scrollButton.classList.toggle('active');
                    }

                    // 시스템 로그를 주기적으로 가져오는 함수
                    async function fetchSystemLogs() {
                        try {
                            const response = await fetch('/api/v1/system/logs');
                            const data = await response.json();
                            
                            if (data.logs) {
                                data.logs.forEach(log => {
                                    addLog(log.message, log.level);
                                });
                            }
                        } catch (error) {
                            console.error('로그 가져오기 실패:', error);
                        }
                    }

                    // 5초마다 로그 업데이트
                    setInterval(fetchSystemLogs, 5000);

                    // ESC 키로 전체화면 해제
                    document.addEventListener('keydown', (e) => {
                        if (e.key === 'Escape' && activeCameraCell) {
                            activeCameraCell.classList.remove('active');
                            activeCameraCell = null;
                        }
                    });
                </script>
            </body>
        </html>
        """
        return html_content
    except Exception:
        return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    html_content = """
    <html>
        <head>
            <title>지켜봄 - 로그인</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Noto Sans KR', sans-serif;
                    background: #f5f5f5;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                
                .login-container {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 400px;
                }
                
                .logo {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    margin-bottom: 32px;
                }
                
                .logo i {
                    font-size: 32px;
                    color: #1a73e8;
                }
                
                .logo span {
                    font-size: 24px;
                    font-weight: 500;
                    color: #1a73e8;
                }
                
                .form-group {
                    margin-bottom: 20px;
                }
                
                .form-group label {
                    display: block;
                    margin-bottom: 8px;
                    color: #5f6368;
                }
                
                .form-group input {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                
                .form-group input:focus {
                    outline: none;
                    border-color: #1a73e8;
                }
                
                .submit-btn {
                    width: 100%;
                    padding: 12px;
                    background: #1a73e8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    cursor: pointer;
                    margin-bottom: 16px;
                }
                
                .submit-btn:hover {
                    background: #1557b0;
                }
                
                .register-link {
                    text-align: center;
                    color: #5f6368;
                }
                
                .register-link a {
                    color: #1a73e8;
                    text-decoration: none;
                }
                
                .register-link a:hover {
                    text-decoration: underline;
                }

                .error-message {
                    color: #d93025;
                    margin-bottom: 16px;
                    display: none;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">
                    <i class="material-icons">visibility</i>
                    <span>지켜봄</span>
                </div>
                <div id="error-message" class="error-message"></div>
                <form id="loginForm">
                    <div class="form-group">
                        <label for="username">사용자명</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">비밀번호</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="submit-btn">로그인</button>
                </form>
                <div class="register-link">
                    계정이 없으신가요? <a href="/register">회원가입</a>
                </div>
            </div>
            
            <script>
                document.getElementById('loginForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: document.getElementById('username').value,
                        password: document.getElementById('password').value
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    window.location.href = '/';
                } else {
                    const errorMessage = document.getElementById('error-message');
                    errorMessage.textContent = data.detail || '로그인에 실패했습니다.';
                    errorMessage.style.display = 'block';
                }
                });
            </script>
        </body>
    </html>
    """
    return html_content


@router.get("/register", response_class=HTMLResponse)
async def register_page():
    html_content = """
    <html>
        <head>
            <title>지켜봄 - 회원가입</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Noto Sans KR', sans-serif;
                    background: #f5f5f5;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                
                .register-container {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 400px;
                }
                
                .logo {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    margin-bottom: 32px;
                }
                
                .logo i {
                    font-size: 32px;
                    color: #1a73e8;
                }
                
                .logo span {
                    font-size: 24px;
                    font-weight: 500;
                    color: #1a73e8;
                }
                
                .form-group {
                    margin-bottom: 20px;
                }
                
                .form-group label {
                    display: block;
                    margin-bottom: 8px;
                    color: #5f6368;
                }
                
                .form-group input {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                
                .form-group input:focus {
                    outline: none;
                    border-color: #1a73e8;
                }
                
                .submit-btn {
                    width: 100%;
                    padding: 12px;
                    background: #1a73e8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    cursor: pointer;
                    margin-bottom: 16px;
                }
                
                .submit-btn:hover {
                    background: #1557b0;
                }
                
                .login-link {
                    text-align: center;
                    color: #5f6368;
                }
                
                .login-link a {
                    color: #1a73e8;
                    text-decoration: none;
                }
                
                .login-link a:hover {
                    text-decoration: underline;
                }

                .error-message {
                    color: #d93025;
                    margin-bottom: 16px;
                    display: none;
                }
            </style>
        </head>
        <body>
            <div class="register-container">
                <div class="logo">
                    <i class="material-icons">visibility</i>
                    <span>지켜봄</span>
                </div>
                <div id="error-message" class="error-message"></div>
                <form id="registerForm">
                    <div class="form-group">
                        <label for="username">사용자명</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">비밀번호</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label for="password2">비밀번호 확인</label>
                        <input type="password" id="password2" name="password2" required>
                    </div>
                    <button type="submit" class="submit-btn">회원가입</button>
                </form>
                <div class="login-link">
                    이미 계정이 있으신가요? <a href="/login">로그인</a>
                </div>
            </div>
            
            <script>
                document.getElementById('registerForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const password = document.getElementById('password').value;
                    const password2 = document.getElementById('password2').value;
                    
                    if (password !== password2) {
                        const errorMessage = document.getElementById('error-message');
                        errorMessage.textContent = '비밀번호가 일치하지 않습니다.';
                        errorMessage.style.display = 'block';
                        return;
                    }
                    
                    const response = await fetch('/api/auth/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            username: document.getElementById('username').value,
                            password: password
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        alert('회원가입이 완료되었습니다.');
                        window.location.href = '/login';
                    } else {
                        const errorMessage = document.getElementById('error-message');
                        errorMessage.textContent = data.detail || '회원가입에 실패했습니다.';
                        errorMessage.style.display = 'block';
                    }
                });
            </script>
        </body>
    </html>
    """
    return html_content