# 산업용 로봇 안전 감지 시스템 웹 환경 개발 계획

## 1. 프로젝트 개요

- **목표**: 로봇 펜스 내부의 안전 감지 시스템을 개발하여, 작동 중인 로봇이 사람을 감지하고 안전모 착용 여부를 확인하여 적절한 알림을 제공.
- **개발 기간**: 1개월
- **개발 환경**: 웹 기반 애플리케이션

## 2. 프로젝트 실행 방법

### 2.1. 사전 요구 사항

- **Docker**: [Docker 공식 사이트](https://www.docker.com/)에서 Docker를 설치하세요.
- **Git**: Git이 설치되어 있지 않다면 [Git 공식 사이트](https://git-scm.com/)에서 설치하세요.

### 2.2. 설치 및 실행

1. **프로젝트 클론**
    ```bash
    git clone <repository_url>
    cd Watcheye
    ```

2. **도커 컴포즈 실행**
    ```bash
    docker-compose down
    sudo docker system prune -a --volumes
    docker-compose up --build
    ```

3. **애플리케이션 접속**
    - 웹 브라우저에서 `http://localhost`에 접속하여 애플리케이션을 사용하세요.

## 3. 추가 개발 필요 사항

- [ ] **로그아웃 기능 추가**
    - 사용자 세션을 종료하고 보안을 강화하기 위한 로그아웃 기능 구현.
  
- [ ] **로그인되지 않은 사용자의 접근 제한**
    - 인증되지 않은 사용자가 `/` 페이지에 접근할 경우 자동으로 `/login` 페이지로 리디렉션하도록 설정.

- [ ] **웹캠 연결**
    - 사용자의 웹캠을 애플리케이션과 연동하여 실시간 영상 스트리밍 기능 구현.

- [ ] **AI 모델 이벤트 발생 시 화면 캡쳐**
    - AI 모델이 특정 이벤트를 감지할 경우 해당 순간의 화면을 자동으로 캡처하는 기능 추가.

- [ ] **로그 기록 및 화면에서 로그 파일 가시화 (수정 불가)**
    - 시스템 로그를 기록하고, 이를 사용자 인터페이스 내에서 실시간으로 확인할 수 있도록 구현. 단, 로그 파일은 수정 불가능하게 설정.

- [ ] **이상 발생 시 문자 알림**
    - 시스템에서 이상 상태가 감지될 경우 관리자에게 자동으로 문자 메시지를 전송하는 알림 기능 추가.

## 4. 기술 스택

- **백엔드**: FastAPI, Uvicorn, SQLAlchemy
- **프론트엔드**: HTML, CSS
- **AI 모델**: PyTorch, TorchVision
- **데이터베이스**: SQLite
- **도커**: Docker, Docker Compose

