# 🚀 Coditor 코드 채점 API 서버

**Coditor 채점 시스템의 MSA 기반 API 서버입니다.**  
코드 채점 요청을 Redis 메시지 브로커 기능을 활용해 Celery 태스크 큐에 등록하고, Celery Worker는 채점 결과를 비동기적(WebHook Callback)으로 전달합니다.

<br /><br />



## 🧱 채점 과정
### 채점 등록/실행/중단 요청 
```
End User -> Spring Boot Backend -> Flask API Server -> Redis
```
- 채점 등록 요청 수신 시, 채점 작업을 생성하고 Redis에 저장합니다.
- 채점 실행 요청 수신 시, Redis 메시지 브로커를 통해 Celery 태스크 큐에 채점 작업을 적재합니다.
- 채점 중단 요청 수신 시, Redis에 저장된 채점 작업에 stop flag를 설정합니다.
- 채점 실행/중단 요청의 실제 처리는 WebHook 방식으로 비동기적으로 처리됩니다.
<br />

### 코드 실행 및 평가
```
Redis -> Celery Worker -> Docker Container
```
- Celery Worker는 Redis 메시지 브로커로부터 작업을 수신하여 언어별 Docker 컨테이너에서 안전하게 실행합니다.
- 실행 중인 작업에 stop flag가 설정된 경우, 채점 작업을 중단합니다.
<br />

### 채점 결과 전달
```
Docker Container -> Celery Worker -> Spring Boot Backend -> End User
```
- 채점 결과는 WebHook 콜백을 통해 Spring Boot 백엔드로 직접 전송됩니다.
- 각 테스트 케이스 결과는 개별적으로 실시간 전송됩니다.
- 엔드 유저는 구독 중인 SSE 세션을 통해 결과를 전달 받습니다.

<br /><br />



## ✨ 주요 기능

- REST API 엔드포인트 제공
- 코드 채점 요청 처리 및 검증
- Redis 태스크 큐에 작업 등록
- 채점 결과 웹훅 콜백 처리
- HMAC 기반 API 키 인증
- Celery 기반 비동기 작업 처리
- Docker 컨테이너 기반 샌드박스 환경 구현
- Java17 한정 채점 서비스 지원
- 실시간 채점 결과 전송
- 테스트 케이스별 상세 결과 제공 (컴파일 에러, 런타임 에러, 시간 초과, 메모리 초과 등)
- 컨테이너 보안정책 적용 (리소스 제한, 네트워크 격리, 시스템 콜 차단 등)
