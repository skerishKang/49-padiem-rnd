import markdown
import os

# 파일 경로 설정
md_file = '최종보고서.md'
html_file = '최종보고서_print.html'

# 마크다운 확장 기능 설정 (표, 코드 하이라이트 등)
extensions = [
    'extra',
    'codehilite',
    'toc',
    'nl2br',
    'sane_lists'
]

# 스타일 시트 (A4 보고서용 정교한 스타일)
css = """
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

:root {
    --primary-color: #2c3e50;
    --border-color: #eee;
}

body {
    font-family: 'Pretendard', 'Malgun Gothic', -apple-system, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 210mm;
    margin: 0 auto;
    padding: 30mm 20mm;
    background-color: white;
}

@media print {
    body {
        padding: 0;
        margin: 0;
    }
    .no-print {
        display: none;
    }
    h1, h2, h3 {
        page-break-after: avoid;
    }
    table, img {
        page-break-inside: avoid;
    }
    a {
        text-decoration: none;
        color: black;
    }
}

h1 {
    font-size: 2.5em;
    color: var(--primary-color);
    border-bottom: 3px solid var(--primary-color);
    padding-bottom: 20px;
    margin-top: 50px;
    text-align: center;
}

h2 {
    font-size: 1.8em;
    color: var(--primary-color);
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 10px;
    margin-top: 40px;
}

h3 {
    font-size: 1.4em;
    margin-top: 30px;
    color: #444;
}

h4 {
    font-size: 1.1em;
    color: #666;
}

p {
    margin-bottom: 1.2em;
    text-align: justify;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 20px auto;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 25px 0;
    font-size: 0.9em;
}

th, td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: left;
}

th {
    background-color: #f8f9fa;
    font-weight: bold;
}

blockquote {
    border-left: 5px solid #ddd;
    padding-left: 20px;
    color: #666;
    margin: 20px 0;
    background: #fdfdfd;
}

code {
    background-color: #f4f4f4;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: Consolas, Monaco, 'Andale Mono', monospace;
}

pre {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 5px;
    overflow-x: auto;
    border: 1px solid #eee;
}

.toc {
    background-color: #f9f9f9;
    padding: 25px;
    border-radius: 8px;
    margin-bottom: 50px;
    border: 1px solid #eee;
}

.toc ul {
    list-style: none;
    padding-left: 0;
}

.toc ul ul {
    padding-left: 20px;
}

.toc a {
    color: #2c3e50;
    text-decoration: none;
}

.toc a:hover {
    text-decoration: underline;
}

/* 안내 배너 */
.no-print-banner {
    background: #fff3cd;
    padding: 15px;
    margin-bottom: 30px;
    border: 1px solid #ffeeba;
    border-radius: 5px;
    text-align: center;
    font-weight: bold;
}
"""

def convert():
    if not os.path.exists(md_file):
        print(f"Error: {md_file} not found.")
        return

    with open(md_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # HTML 변환
    html_body = markdown.markdown(text, extensions=extensions)

    # 전체 HTML 템플릿 결합
    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>최종보고서 - PDF 변환용</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="no-print no-print-banner">
        💡 이 페이지에서 <b>Ctrl + P</b>를 누른 후 'PDF로 저장'을 선택하세요. <br>
        (배경 그래픽 포함 옵션을 켜면 더 깔끔하게 나옵니다.)
    </div>
    {html_body}
</body>
</html>
"""

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"Success: {html_file} created.")

if __name__ == "__main__":
    convert()
