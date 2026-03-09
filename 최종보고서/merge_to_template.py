import markdown
import os
import re

# 파일 경로 설정
md_file = '최종보고서_본문.md'
template_file = '최종보고서_양식.html'
output_file = '최종보고서_최종_양식.html'

# 마크다운 확장 기능 설정
extensions = [
    'extra',
    'codehilite',
    'toc',
    'nl2br',
    'sane_lists'
]

def merge():
    if not os.path.exists(md_file) or not os.path.exists(template_file):
        print("Error: Required files missing.")
        return

    # 마크다운 읽기
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 템플릿 읽기
    with open(template_file, 'r', encoding='utf-8') as f:
        template_text = f.read()

    # 마크다운을 HTML로 변환
    content_html = markdown.markdown(md_text, extensions=extensions)

    # 각 H1(장)마다 새로운 'page' div로 감싸기 위해 분할
    # 주의: 마크다운 변환 결과 h1 태그를 기준으로 페이지를 나눕니다.
    sections = re.split(r'(<h1[^>]*>.*?</h1>)', content_html, flags=re.DOTALL)
    
    processed_html = ""
    current_page_content = ""
    
    for part in sections:
        if part.startswith('<h1'):
            # 새 장이 시작되기 전, 이전 내용이 있다면 페이지로 감싸기
            if current_page_content.strip():
                processed_html += f'<div class="page"><div class="content">{current_page_content}</div></div>\n'
            current_page_content = part # 제목부터 다시 시작
        else:
            current_page_content += part

    # 마지막 섹션 추가
    if current_page_content.strip():
        processed_html += f'<div class="page"><div class="content">{current_page_content}</div></div>\n'

    # 템플릿의 {{CONTENT}} 치환
    final_html = template_text.replace('{{CONTENT}}', processed_html)

    # 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Success: {output_file} created.")

if __name__ == "__main__":
    merge()
