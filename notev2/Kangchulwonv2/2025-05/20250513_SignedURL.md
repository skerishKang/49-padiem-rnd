---
📅 **날짜**: 2025년 5월 13일 (화)
👤 **작성자**: 강철원 (연구책임자) | **승인**: 강혜림 (대표)
📊 **진행 단계**: 3단계 - 고도화 및 사업화
🎯 **주요 작업**: Signed URL 구현 및 적용
---

# AI 기반 다국어 음성 합성 및 실시간 립싱크 더빙 시스템 개발일지

## 📋 오늘의 작업 내용

### 1. Signed URL 생성

- **목적**: 유료 콘텐츠 보호. CloudFront Key Pair를 사용하여 서명된 URL 생성.
- **유효 기간**: 영상 재생 길이를 고려하여 1시간으로 설정.

### 2. 프론트엔드 적용

- 기존 S3 URL(`s3.ap-northeast-2.amazonaws.com/...`)을 CloudFront URL(`cdn.padiem.com/...`)로 교체.
- **성능 측정**: 미국 리전 VPN 접속 후 로딩 속도 비교. -> 평균 1.5초에서 0.3초로 단축.

## 🔧 기술적 진행사항

### Python 서명 코드

```python
from botocore.signers import CloudFrontSigner

def rsa_signer(message):
    with open('private_key.pem', 'rb') as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

signer = CloudFrontSigner(key_id, rsa_signer)
url = signer.generate_presigned_url(url, date_less_than=expire_date)
```

## 📊 진행 상황

| 항목 | 계획 | 실제 | 상태 |
|------|------|------|------|
| Signed URL 구현 | 완료 | 완료 | ✅ |
| 성능 테스트 | 완료 | 완료 | ✅ |

## 🚧 이슈 사항 및 해결 방안

- **Key 관리**: Private Key 파일 보안 중요. -> AWS Secrets Manager에 저장하고 런타임에 로드하여 사용.

## 📝 내일 계획

1. S3 Transfer Acceleration 설정
2. 대용량 파일 업로드 테스트

---

## 📚 참고 자료

- [1] "Serving Private Content with Signed URLs". [Link](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html)

<details>
<summary>IRIS 붙여넣기용 HTML 코드</summary>

```html
<h3>1. Signed URL 생성</h3>
<ul>
<li><strong>목적</strong>: 유료 콘텐츠 보호. CloudFront Key Pair를 사용하여 서명된 URL 생성.</li>
<li><strong>유효 기간</strong>: 영상 재생 길이를 고려하여 1시간으로 설정.</li>
</ul>
<h3>2. 프론트엔드 적용</h3>
<ul>
<li>기존 S3 URL(<code>s3.ap-northeast-2.amazonaws.com/...</code>)을 CloudFront URL(<code>cdn.padiem.com/...</code>)로 교체.</li>
<li><strong>성능 측정</strong>: 미국 리전 VPN 접속 후 로딩 속도 비교. -&gt; 평균 1.5초에서 0.3초로 단축.</li>
</ul>
```

</details>
