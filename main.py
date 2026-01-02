import csv
import json
import os

# 파일 설정
INPUT_FILE = 'events.csv'
OUTPUT_FILE = 'index.html'

def read_csv_data(filename):
    events = []
    if not os.path.exists(filename):
        print(f"오류: {filename} 파일이 존재하지 않습니다.")
        return []

    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 데이터 정제
            end_date = row['종료일']
            if len(end_date) <= 10: # 'YYYY-MM-DD' 형식인 경우 23:59:59 추가
                end_date += " 23:59:59"
            
            row['js_end_date'] = end_date
            events.append(row)
    return events

def generate_html(events):
    # Python 데이터를 JSON 문자열로 변환하여 JS 변수에 주입
    events_json = json.dumps(events, ensure_ascii=False)

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>방갤 갤 대회 목록 대시보드</title>
    <style>
        :root {{
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --primary: #333333;
            --secondary: #666666;
            --border: #e0e0e0;
            --shadow: 0 4px 6px rgba(0,0,0,0.1);
            --hover-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}

        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--primary);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--border);
            flex-wrap: wrap;
            gap: 15px;
        }}

        h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
        }}

        .status-bar {{
            display: flex;
            gap: 20px;
            align-items: center;
            font-size: 14px;
            font-weight: 500;
        }}

        .current-time {{
            color: var(--secondary);
            font-family: monospace;
            font-size: 16px;
        }}

        .controls {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        select {{
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background-color: var(--card-bg);
            font-size: 14px;
            cursor: pointer;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            flex: 1;
        }}

        .card {{
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: var(--hover-shadow);
            border-color: #333;
        }}

        .card-header {{
            margin-bottom: 15px;
        }}

        .card-title {{
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 8px 0;
            word-break: keep-all;
        }}

        .organizer {{
            font-size: 13px;
            color: var(--secondary);
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .card-body {{
            margin-top: auto;
        }}

        .dates {{
            font-size: 13px;
            color: var(--secondary);
            margin-bottom: 15px;
            background: #f1f1f1;
            padding: 8px;
            border-radius: 6px;
        }}

        .date-row {{
            display: flex;
            justify-content: space-between;
        }}

        .timer-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
            color: white;
            width: fit-content;
        }}

        /* 상태별 색상 정의 */
        .timer-badge.ended {{
            background-color: var(--secondary);
        }}
        
        /* 3일 미만: 엄청 빨간색 + 펄스 애니메이션 */
        .timer-badge.critical {{
            background-color: #d32f2f; 
            animation: pulse 2s infinite;
        }}

        /* 7일 미만: 주황색 */
        .timer-badge.warning {{
            background-color: #f57c00;
        }}

        /* 30일 미만: 노란색 (가독성을 위해 글자색 검정) */
        .timer-badge.notice {{
            background-color: #fbc02d;
            color: #333333;
        }}

        /* 30일 이상: 초록색 */
        .timer-badge.safe {{
            background-color: #388e3c;
        }}

        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
            100% {{ opacity: 1; }}
        }}

        footer {{
            margin-top: 40px;
            padding-top: 20px;
            padding-bottom: 10px;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--secondary);
            font-size: 14px;
            font-weight: 500;
        }}

    </style>
</head>
<body>

<div class="container">
    <header>
        <div>
            <h1>방갤 갤 대회 목록 대시보드</h1>
        </div>
        <div class="status-bar">
            <div id="clock" class="current-time">로딩 중...</div>
            <div class="controls">
                <label for="sortSelect">정렬:</label>
                <select id="sortSelect" onchange="renderEvents()">
                    <option value="endingSoon">마감 임박순 (기본)</option>
                    <option value="startDate">시작일 순</option>
                    <option value="title">제목 순</option>
                </select>
            </div>
        </div>
    </header>

    <div id="eventGrid" class="grid">
        </div>

    <footer>
        made by Bangbung Kim
    </footer>
</div>

<script>
    const events = {events_json};

    function updateClock() {{
        const now = new Date();
        const options = {{ 
            year: 'numeric', month: 'long', day: 'numeric', 
            hour: '2-digit', minute: '2-digit', second: '2-digit',
            hour12: false 
        }};
        document.getElementById('clock').innerText = now.toLocaleString('ko-KR', options);
    }}

    function getRemainingTime(endDateStr) {{
        const now = new Date();
        const end = new Date(endDateStr.replace(' ', 'T'));
        const diff = end - now;

        if (diff < 0) {{
            return {{ status: 'ended', text: '종료됨' }};
        }}

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

        let text = '';
        if (days > 0) text += days + '일 ';
        text += hours + '시간 ';
        text += minutes + '분 남음';

        // 상태 결정 로직
        let status = '';
        if (days < 3) {{
            status = 'critical'; // 빨강
        }} else if (days < 7) {{
            status = 'warning';  // 주황
        }} else if (days < 30) {{
            status = 'notice';   // 노랑
        }} else {{
            status = 'safe';     // 초록
        }}
        
        return {{ status: status, text: text, diff: diff }};
    }}

    function renderEvents() {{
        const grid = document.getElementById('eventGrid');
        const sortType = document.getElementById('sortSelect').value;
        grid.innerHTML = '';

        const sortedEvents = [...events].sort((a, b) => {{
            if (sortType === 'endingSoon') {{
                const timeA = new Date(a.js_end_date.replace(' ', 'T'));
                const timeB = new Date(b.js_end_date.replace(' ', 'T'));
                const now = new Date();
                
                const diffA = timeA - now;
                const diffB = timeB - now;
                
                const valA = diffA < 0 ? 9999999999999 : diffA;
                const valB = diffB < 0 ? 9999999999999 : diffB;
                
                return valA - valB;
            }} else if (sortType === 'startDate') {{
                return new Date(a.시작일) - new Date(b.시작일);
            }} else if (sortType === 'title') {{
                return a.제목.localeCompare(b.제목);
            }}
        }});

        sortedEvents.forEach(evt => {{
            const remaining = getRemainingTime(evt.js_end_date);
            
            const card = document.createElement('a');
            card.className = 'card';
            card.href = evt.링크;
            card.target = '_blank';

            card.innerHTML = `
                <div class="card-header">
                    <h3 class="card-title">${{evt.제목}}</h3>
                    <div class="organizer">
                        <span>주최: ${{evt.주최자_닉}} (${{evt.주최자_식별코드}})</span>
                    </div>
                </div>
                <div class="card-body">
                    <div class="dates">
                        <div class="date-row"><span>시작:</span> <span>${{evt.시작일}}</span></div>
                        <div class="date-row"><span>종료:</span> <span>${{evt.종료일}}</span></div>
                    </div>
                    <div class="timer-badge ${{remaining.status}}">
                        ${{remaining.text}}
                    </div>
                </div>
            `;
            grid.appendChild(card);
        }});
    }}

    setInterval(updateClock, 1000);
    updateClock();
    renderEvents();
    setInterval(renderEvents, 60000);

</script>
</body>
</html>
    """
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"성공적으로 {OUTPUT_FILE} 파일이 생성되었습니다.")

if __name__ == "__main__":
    data = read_csv_data(INPUT_FILE)
    if data:
        generate_html(data)