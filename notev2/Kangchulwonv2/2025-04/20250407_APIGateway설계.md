---
📅 **날짜**: 2025년 4월 7일 (월)
👤 **작성자**: 강철원 (연구책임자) | **승인**: 강혜림 (대표)
📊 **진행 단계**: 3단계 - 고도화 및 사업화
🎯 **주요 작업**: B2B API Gateway 설계
---

# AI 기반 다국어 음성 합성 및 실시간 립싱크 더빙 시스템 개발일지

## 📋 오늘의 작업 내용

### 1. API Gateway 필요성

- 기업 고객(B2B)에게 더빙 기능을 API로 제공하기 위함.
- **기능**: 인증(Authentication), 속도 제한(Rate Limiting), 사용량 집계(Metering), 라우팅.

### 2. 솔루션 선정

- **AWS API Gateway**: 완전 관리형 서비스, 확장성 좋음, 비용 발생.
- **Kong (Open Source)**: 커스터마이징 용이, 직접 구축 필요.
- **결정**: 초기 구축 비용 절감 및 유연성을 위해 **Kong (Docker)** 도입.

## 🔧 기술적 진행사항

### Kong 설정 (docker-compose)

```yaml
services:
  kong:
    image: kong:latest
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: db
      KONG_PROXY_ACCESS_LOG: /dev/stdout
    ports:
      - "8000:8000"
      - "8001:8001" # Admin API
```

## 📊 진행 상황

| 항목 | 계획 | 실제 | 상태 |
|------|------|------|------|
| 솔루션 선정 | 완료 | 완료 | ✅ |
| Kong 설치 | 완료 | 완료 | ✅ |

## 🚧 이슈 사항 및 해결 방안

- **DB 의존성**: Kong은 메타데이터 저장을 위해 DB가 필요함. -> 기존 PostgreSQL에 `kong` 스키마 추가하여 활용.

## 📝 내일 계획

1. API Key 발급 시스템 개발
2. Kong 플러그인 설정 (Key Auth, Rate Limiting)

---

## 📚 참고 자료

- [1] "Kong Gateway". [Link](https://docs.konghq.com/gateway/latest/)

<details>
<summary>IRIS 붙여넣기용 HTML 코드</summary>

```html
<h3>1. API Gateway 필요성</h3>
<ul>
<li>기업 고객(B2B)에게 더빙 기능을 API로 제공하기 위함.</li>
<li><strong>기능</strong>: 인증(Authentication), 속도 제한(Rate Limiting), 사용량 집계(Metering), 라우팅.</li>
</ul>
<h3>2. 솔루션 선정</h3>
<ul>
<li><strong>AWS API Gateway</strong>: 완전 관리형 서비스, 확장성 좋음, 비용 발생.</li>
<li><strong>Kong (Open Source)</strong>: 커스터마이징 용이, 직접 구축 필요.</li>
<li><strong>결정</strong>: 초기 구축 비용 절감 및 유연성을 위해 <strong>Kong (Docker)</strong> 도입.</li>
</ul>
```

</details>
