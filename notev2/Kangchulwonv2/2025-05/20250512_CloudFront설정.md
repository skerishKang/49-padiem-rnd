---
📅 **날짜**: 2025년 5월 12일 (월)
👤 **작성자**: 강철원 (연구책임자) | **승인**: 강혜림 (대표)
📊 **진행 단계**: 3단계 - 고도화 및 사업화
🎯 **주요 작업**: AWS CloudFront 설정
---

# AI 기반 다국어 음성 합성 및 실시간 립싱크 더빙 시스템 개발일지

## 📋 오늘의 작업 내용

### 1. CloudFront 배포 생성

- **Origin Domain**: S3 버킷 도메인 선택.
- **OAC (Origin Access Control)**: S3 버킷에 직접 접근을 막고 CloudFront를 통해서만 접근하도록 설정. (기존 OAI보다 보안 강화됨)
- **Viewer Protocol Policy**: Redirect HTTP to HTTPS.

### 2. S3 버킷 정책 업데이트

- CloudFront의 OAC가 S3 객체를 읽을 수 있도록 `GetObject` 권한 부여.

## 🔧 기술적 진행사항

### Bucket Policy (JSON)

```json
{
    "Version": "2012-10-17",
    "Statement": {
        "Sid": "AllowCloudFrontServicePrincipalReadOnly",
        "Effect": "Allow",
        "Principal": {
            "Service": "cloudfront.amazonaws.com"
        },
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::padiem-assets/*",
        "Condition": {
            "StringEquals": {
                "AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/EDFDVBD632BHDS5"
            }
        }
    }
}
```

## 📊 진행 상황

| 항목 | 계획 | 실제 | 상태 |
|------|------|------|------|
| CloudFront 생성 | 완료 | 완료 | ✅ |
| 정책 설정 | 완료 | 완료 | ✅ |

## 🚧 이슈 사항 및 해결 방안

- **배포 시간**: CloudFront 배포 생성에 약 15분 소요. -> 대기 시간 동안 문서 정리.

## 📝 내일 계획

1. Signed URL 생성 로직 구현
2. 프론트엔드 영상 소스 URL 교체

---

## 📚 참고 자료

- [1] "Restricting Access to Amazon S3 Content". [Link](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)

<details>
<summary>IRIS 붙여넣기용 HTML 코드</summary>

```html
<h3>1. CloudFront 배포 생성</h3>
<ul>
<li><strong>Origin Domain</strong>: S3 버킷 도메인 선택.</li>
<li><strong>OAC (Origin Access Control)</strong>: S3 버킷에 직접 접근을 막고 CloudFront를 통해서만 접근하도록 설정. (기존 OAI보다 보안 강화됨)</li>
<li><strong>Viewer Protocol Policy</strong>: Redirect HTTP to HTTPS.</li>
</ul>
<h3>2. S3 버킷 정책 업데이트</h3>
<ul>
<li>CloudFront의 OAC가 S3 객체를 읽을 수 있도록 <code>GetObject</code> 권한 부여.</li>
</ul>
```

</details>
