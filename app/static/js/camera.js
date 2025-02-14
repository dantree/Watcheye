// 카메라 선택 처리
document.querySelector('.select').addEventListener('change', function(e) {
    const selectedCamera = e.target.value;
    const cameraElements = document.querySelectorAll('[class^="div-"][class*="2"]');
    
    if (selectedCamera === 'all') {
        cameraElements.forEach(el => el.style.display = 'block');
    } else {
        cameraElements.forEach(el => {
            const cameraId = el.querySelector('img').getAttribute('data-camera-id');
            el.style.display = cameraId === selectedCamera ? 'block' : 'none';
        });
    }
});

// 전체화면 처리
document.querySelector('.button-2').addEventListener('click', function() {
    const mainContent = document.querySelector('.div-11');
    if (!document.fullscreenElement) {
        mainContent.requestFullscreen().catch(err => {
            console.error(`전체화면 에러: ${err.message}`);
        });
    } else {
        document.exitFullscreen();
    }
});

// 카메라 스트림 에러 처리
document.querySelectorAll('img[src*="/stream"]').forEach(img => {
    img.onerror = function() {
        const noSignalPath = window.location.origin + '/static/images/no-signal.png';
        this.src = noSignalPath;
        const container = this.closest('.camera-container');
        container.querySelector('.camera-offline').style.display = 'flex';
    };
});

// 카메라 연결 버튼 이벤트 처리
document.querySelectorAll('.connect-camera-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
        const container = this.closest('.camera-container');
        const img = container.querySelector('img');
        const cameraId = img.getAttribute('data-camera-id');
        
        try {
            // 카메라 연결 시도
            const response = await fetch(`/api/v1/cameras/${cameraId}/connect`, {
                method: 'POST'
            });
            
            if (response.ok) {
                // 연결 성공 시 스트림 재시도
                const timestamp = new Date().getTime();
                img.src = `/api/v1/cameras/${cameraId}/stream?t=${timestamp}`;
                container.querySelector('.camera-offline').style.display = 'none';
            } else {
                throw new Error('카메라 연결 실패');
            }
        } catch (error) {
            console.error('카메라 연결 오류:', error);
            alert('카메라 연결에 실패했습니다. 다시 시도해주세요.');
        }
    });
});

// 디바이스 연결 버튼 이벤트 처리
document.querySelectorAll('.device-connect-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
        const cameraId = this.getAttribute('data-camera-id');
        
        try {
            // 사용 가능한 카메라 디바이스 목록 가져오기
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            if (videoDevices.length === 0) {
                alert('사용 가능한 카메라 디바이스가 없습니다.');
                return;
            }
            
            // 디바이스 선택 다이얼로그 생성
            const deviceSelect = document.createElement('select');
            deviceSelect.innerHTML = videoDevices.map(device => 
                `<option value="${device.deviceId}">${device.label || `카메라 ${device.deviceId.slice(0, 8)}...`}</option>`
            ).join('');
            
            const result = await new Promise(resolve => {
                const dialog = document.createElement('div');
                dialog.className = 'device-select-dialog';
                dialog.innerHTML = `
                    <div class="dialog-content">
                        <h3>카메라 디바이스 선택</h3>
                        ${deviceSelect.outerHTML}
                        <div class="dialog-buttons">
                            <button class="confirm-btn">연결</button>
                            <button class="cancel-btn">취소</button>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(dialog);
                
                dialog.querySelector('.confirm-btn').onclick = () => {
                    const selectedDeviceId = dialog.querySelector('select').value;
                    dialog.remove();
                    resolve(selectedDeviceId);
                };
                
                dialog.querySelector('.cancel-btn').onclick = () => {
                    dialog.remove();
                    resolve(null);
                };
            });
            
            if (result) {
                // 선택한 디바이스로 카메라 연결 시도
                const response = await fetch(`/api/v1/cameras/${cameraId}/connect-device`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ deviceId: result })
                });
                
                if (response.ok) {
                    // 연결 성공 시 스트림 재시도
                    const timestamp = new Date().getTime();
                    const container = this.closest('.camera-container');
                    const img = container.querySelector('img');
                    img.src = `/api/v1/cameras/${cameraId}/stream?t=${timestamp}`;
                    container.querySelector('.camera-offline').style.display = 'none';
                } else {
                    throw new Error('디바이스 연결 실패');
                }
            }
        } catch (error) {
            console.error('디바이스 연결 오류:', error);
            alert('카메라 디바이스 연결에 실패했습니다. 다시 시도해주세요.');
        }
    });
}); 