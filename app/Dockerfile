# 기본 이미지로 Python 3.9 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 필요한 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# PyTorch CPU 버전 설치
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 애플리케이션 코드 복사
COPY . .

# 템플릿 디렉토리 생성
RUN mkdir -p /app/templates

# 정적 파일 디렉토리 생성
RUN mkdir -p /app/static/css \
    && mkdir -p /app/static/js \
    && mkdir -p /app/static/images \
    && mkdir -p /app/captures

# 실행 권한 설정
RUN chmod -R 755 /app

# PYTHONPATH 설정
# ENV PYTHONPATH=/app
# 포트 설정
EXPOSE 8001

# 실행 명령
CMD ["python", "-m", "src.main"] 