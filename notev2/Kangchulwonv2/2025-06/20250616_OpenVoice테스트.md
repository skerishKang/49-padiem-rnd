---
📅 **날짜**: 2025년 6월 16일 (월)
👤 **작성자**: 강철원 (연구책임자) | **승인**: 강혜림 (대표)
📊 **진행 단계**: 3단계 - 시스템 통합 및 고도화
🎯 **주요 작업**: VALL-E X 성능 최적화
---

# AI 기반 다국어 음성 합성 및 실시간 립싱크 더빙 시스템 개발일지

## 📋 오늘의 작업 내용

### 1. 추론 속도 개선

- **문제**: 긴 문장 합성 시 시간이 오래 걸림 (RTF > 3.0).
- **해결**: 문장을 어절 단위로 쪼개서 병렬 처리(Batch Processing) 시도.
- **결과**: RTF 1.5 수준으로 단축.

### 2. 메모리 최적화

- 모델 양자화(Quantization) 검토. `float32` -> `float16` 변환.
- VRAM 사용량 30% 감소 확인.

## 🔧 기술적 진행사항

### Mixed Precision

```python
with torch.cuda.amp.autocast():
    audio = model.inference(text, prompt)
```

## 📊 진행 상황

| 항목 | 계획 | 실제 | 상태 |
|------|------|------|------|
| 속도 개선 | 완료 | 완료 | ✅ |
| 메모리 최적화 | 완료 | 완료 | ✅ |

## 🚧 이슈 사항 및 해결 방안

- **음질 저하**: 양자화 적용 시 미세한 음질 저하 발생. -> 중요도에 따라 옵션 제공 (High Quality vs Fast Speed).

## 📝 내일 계획

1. RVC 모델 파라미터 튜닝
2. 다양한 화자 테스트

---

## 📚 참고 자료

- [1] "PyTorch AMP". [Link](https://pytorch.org/docs/stable/amp.html)

<details>
<summary>IRIS 붙여넣기용 HTML 코드</summary>

```html
<h3>1. 추론 속도 개선</h3>
<ul>
<li><strong>문제</strong>: 긴 문장 합성 시 시간이 오래 걸림 (RTF &gt; 3.0).</li>
<li><strong>해결</strong>: 문장을 어절 단위로 쪼개서 병렬 처리(Batch Processing) 시도.</li>
<li><strong>결과</strong>: RTF 1.5 수준으로 단축.</li>
</ul>
<h3>2. 메모리 최적화</h3>
<ul>
<li>모델 양자화(Quantization) 검토. <code>float32</code> -&gt; <code>float16</code> 변환.</li>
<li>VRAM 사용량 30% 감소 확인.</li>
</ul>
```

</details>
