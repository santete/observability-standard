import os

def md_to_html(md_path, html_path, title):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Escape backticks and also escape script tags just in case
    safe_content = content.replace('`', '&#96;').replace('</script>', '<\\/script>')
    
    html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 1000px; margin: 0 auto; padding: 2rem; color: #333; }}
        pre {{ background: #1e1e1e; color: #d4d4d4; padding: 1.5rem; border-radius: 8px; overflow-x: auto; }}
        code {{ font-family: 'Fira Code', Consolas, monospace; }}
        p > code, li > code {{ background: #f4f4f4; color: #d63384; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.9em; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        th, td {{ border: 1px solid #e2e8f0; padding: 12px; text-align: left; }}
        th {{ background-color: #f8fafc; font-weight: 600; color: #475569; }}
        blockquote {{ border-left: 4px solid #cbd5e1; margin-left: 0; padding: 1rem 1.5rem; color: #475569; background: #f8fafc; border-radius: 0 8px 8px 0; }}
        .mermaid {{ text-align: center; margin: 2rem 0; padding: 1rem; background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; }}
        
        /* Github Alert styling */
        .markdown-alert {{ border-left: 4px solid; padding: 1rem 1.5rem; margin-bottom: 1.5rem; border-radius: 0 8px 8px 0; background-color: #f6f8fa; }}
        .markdown-alert-note {{ border-color: #0969da; }}
        .markdown-alert-tip {{ border-color: #1a7f37; background-color: #e6ffec; }}
        .markdown-alert-important {{ border-color: #8250df; background-color: #f3e8fd; }}
        .markdown-alert-warning {{ border-color: #9a6700; background-color: #fff8c5; }}
        .markdown-alert-caution {{ border-color: #d1242f; background-color: #ffebe9; }}
        
        h1 {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; color: #0f172a; }}
        h2 {{ border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5rem; margin-top: 2.5rem; color: #1e293b; }}
        h3 {{ margin-top: 2rem; color: #334155; }}
    </style>
    <!-- Use specific older version of marked to ensure compatibility with our custom renderer -->
    <script src="https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
</head>
<body>
    <div id="content" style="display:none;"></div>
    <div id="loading" style="text-align:center; padding: 5rem; font-size: 1.2rem; color: #666;">Đang tải tài liệu...</div>
    
    <script type="text/markdown" id="md-raw">{safe_content}</script>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                // Use textContent to avoid innerHTML escaping issues
                let raw = document.getElementById('md-raw').textContent.replace(/&#96;/g, '`');
                
                // Pre-process GitHub Alerts before marked parses them (since blockquote custom renderer can be tricky)
                raw = raw.replace(/> \\\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\\\]/gi, function(match, type) {{
                    return "> **" + type.toUpperCase() + "**\\n>";
                }});
                
                // Renderer to handle mermaid code blocks
                const renderer = new marked.Renderer();
                const originalCodeRenderer = renderer.code.bind(renderer);
                renderer.code = function(code, language, isEscaped) {{
                    if (language === 'mermaid') {{
                        return '<div class="mermaid">' + code + '</div>';
                    }}
                    return originalCodeRenderer(code, language, isEscaped);
                }};
                
                marked.setOptions({{ renderer: renderer, breaks: true, gfm: true }});
                
                const htmlContent = marked.parse(raw);
                document.getElementById('content').innerHTML = htmlContent;
                
                // Post-process blockquotes for alerts
                document.querySelectorAll('blockquote').forEach(bq => {{
                    const firstStrong = bq.querySelector('p strong:first-child');
                    if (firstStrong) {{
                        const type = firstStrong.textContent.trim().toUpperCase();
                        if (['NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION'].includes(type)) {{
                            bq.classList.add('markdown-alert', 'markdown-alert-' + type.toLowerCase());
                            firstStrong.style.color = 'inherit';
                        }}
                    }}
                }});
                
                mermaid.initialize({{ startOnLoad: true, theme: 'default', securityLevel: 'loose' }});
                
                // Show content
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';
            }} catch (error) {{
                document.getElementById('loading').innerHTML = '<span style="color:red;">Lỗi hiển thị tài liệu: ' + error.message + '</span>';
                console.error(error);
            }}
        }});
    </script>
</body>
</html>'''
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

md_to_html('docs/ARCHITECTURE_STANDARD.md', 'docs/ARCHITECTURE_STANDARD.html', 'Kiến Trúc Tiêu Chuẩn')
md_to_html('docs/OBSERVABILITY_STANDARD.md', 'docs/OBSERVABILITY_STANDARD.html', 'Tiêu Chuẩn Observability')
md_to_html('docs/RUNBOOK_TEMPLATE.md', 'docs/RUNBOOK_TEMPLATE.html', 'Sổ Tay Xử Lý Sự Cố')
