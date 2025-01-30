# 기본 이미지로 Python 3.9 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 필요한 Python 패키지들을 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 소스 코드 복사
COPY . .

# 포트 설정
EXPOSE 8001

# 실행 명령
CMD ["python", "-m", "main.py"] 