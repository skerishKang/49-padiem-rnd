---
📅 **날짜**: 2025년 3월 17일 (월)
👤 **작성자**: 강철원 (연구책임자) | **승인**: 강혜림 (대표)
📊 **진행 단계**: 3단계 - 시스템 통합
🎯 **주요 작업**: Streamlit 기획
---

# AI 기반 다국어 음성 합성 및 실시간 립싱크 더빙 시스템 개발일지

## 📋 오늘의 작업 내용

### 1. UI 레이아웃 설계

- **Sidebar**: 메뉴 (Home, Dubbing, History, Settings).
- **Main**:
  - Step 1: 비디오 업로드 (Drag & Drop).
  - Step 2: 언어 선택 및 옵션 (GFPGAN 사용 여부).
  - Step 3: 처리 시작 버튼.
  - Step 4: 진행률 표시 (Progress Bar).
  - Step 5: 결과 영상 재생 및 다운로드.

### 2. Streamlit 구조

- `frontend/app.py`: 메인 엔트리.
- `frontend/pages/`: 페이지별 로직 분리.

## 🔧 기술적 진행사항

### Layout

- Simple and intuitive flow.

## 📊 진행 상황

| 항목 | 계획 | 실제 | 상태 |
|------|------|------|------|
| 기획 | 완료 | 완료 | ✅ |
| 구조 잡기 | 완료 | 완료 | ✅ |

## 🚧 이슈 사항 및 해결 방안

- **특이사항 없음**.

## 📝 내일 계획

1. 기본 UI 구현
2. API 연동 (requests)

---

## 📚 참고 자료

- [1] "Streamlit Layouts".

<details>
<summary>IRIS 붙여넣기용 HTML 코드</summary>

```html
<h3>1. UI 레이아웃 설계</h3>
<ul>
<li><strong>Sidebar</strong>: 메뉴 (Home, Dubbing, History, Settings).</li>
<li><strong>Main</strong>:
<ul>
<li>Step 1: 비디오 업로드 (Drag & Drop).</li>
<li>Step 2: 언어 선택 및 옵션 (GFPGAN 사용 여부).</li>
<li>Step 3: 처리 시작 버튼.</li>
<li>Step 4: 진행률 표시 (Progress Bar).</li>
<li>Step 5: 결과 영상 재생 및 다운로드.</li>
</ul>
</li>
</ul>
<h3>2. Streamlit 구조</h3>
<ul>
<li><code>frontend/app.py</code>: 메인 엔트리.</li>
<li><code>frontend/pages/</code>: 페이지별 로직 분리.</li>
</ul>
```

</details>
