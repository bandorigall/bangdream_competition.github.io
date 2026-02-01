import pandas as pd
import json
import os
from datetime import datetime

# 파일 설정
INPUT_FILE = 'events.csv'
OUTPUT_FILE = 'index.html'
KLOLMAN_FILE = 'klolman_list.py'

def process_events():
    if not os.path.exists(INPUT_FILE):
        print(f"오류: {INPUT_FILE} 파일이 없습니다.")
        return

    # 1. Pandas로 CSV 읽기
    try:
        df = pd.read_csv(INPUT_FILE, encoding='utf-8')
    except Exception as e:
        print(f"CSV 읽기 실패: {e}")
        return

    # 데이터 전처리: 종료일 결측치 처리
    df['종료일'] = df['종료일'].fillna('') 
    
    # 2. 날짜 형식 보정 및 표준화
    def standardize_date(date_str):
        date_str = str(date_str).strip()
        if not date_str:
            return None
        
        # 이미 시간 정보가 포함되어 있는지 확인
        try:
            # Pandas의 유연한 파싱 능력을 활용
            dt = pd.to_datetime(date_str)
            
            # 만약 시/분 정보가 00:00이라면 (날짜만 입력된 경우로 간주) 23:59:59로 설정
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt
        except:
            return None

    # 모든 날짜를 Timestamp 객체로 변환 (비교 및 출력 표준화용)
    df['parsed_end_time'] = df['종료일'].apply(standardize_date)
    
    # ---------------------------------------------------------
    # 기능 1: klolman_list.py 생성 (생략 - 기존 로직 유지)
    # ---------------------------------------------------------
    
    # ---------------------------------------------------------
    # 기능 2: index.html 생성 (표준화된 시간 포맷 사용)
    # ---------------------------------------------------------
    # JavaScript에서 안전하게 인식할 수 있도록 ISO 포맷(YYYY-MM-DDTHH:mm:ss)으로 변환
    df['js_end_date'] = df['parsed_end_time'].apply(
        lambda x: x.strftime('%Y-%m-%dT%H:%M:%S') if pd.notnull(x) else ''
    )
    
    # ★★★ 핵심 수정: JSON 변환 오류를 일으키는 Timestamp 객체 컬럼 삭제 ★★★
    df = df.drop(columns=['parsed_end_time'])
    
    # 딕셔너리 변환 및 JSON 직렬화
    events_list = df.to_dict(orient='records')
    events_json = json.dumps(events_list, ensure_ascii=False)

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
        h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
        .status-bar {{ display: flex; gap: 20px; align-items: center; font-size: 14px; font-weight: 500; }}
        .current-time {{ color: var(--secondary); font-family: monospace; font-size: 16px; }}
        .controls {{ display: flex; align-items: center; gap: 10px; }}
        select {{ padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; background-color: var(--card-bg); font-size: 14px; cursor: pointer; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; flex: 1; }}
        .card {{
            background-color: var(--card-bg); border-radius: 12px; padding: 20px;
            box-shadow: var(--shadow); transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer; border: 1px solid var(--border);
            display: flex; flex-direction: column; position: relative;
            overflow: hidden; text-decoration: none; color: inherit;
        }}
        .card:hover {{ transform: translateY(-5px); box-shadow: var(--hover-shadow); border-color: #333; }}
        .card-header {{ margin-bottom: 15px; }}
        .card-title {{ font-size: 18px; font-weight: 700; margin: 0 0 8px 0; word-break: keep-all; }}
        .organizer {{ font-size: 13px; color: var(--secondary); display: flex; align-items: center; gap: 5px; }}
        .card-body {{ margin-top: auto; }}
        .dates {{ font-size: 13px; color: var(--secondary); margin-bottom: 15px; background: #f1f1f1; padding: 8px; border-radius: 6px; }}
        .date-row {{ display: flex; justify-content: space-between; }}
        .timer-badge {{ display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: 700; color: white; width: fit-content; }}
        .timer-badge.ended {{ background-color: var(--secondary); }}
        .timer-badge.critical {{ background-color: #d32f2f; animation: pulse 2s infinite; }}
        .timer-badge.warning {{ background-color: #f57c00; }}
        .timer-badge.notice {{ background-color: #fbc02d; color: #333333; }}
        .timer-badge.safe {{ background-color: #388e3c; }}
        @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.8; }} 100% {{ opacity: 1; }} }}
        footer {{ margin-top: 40px; padding-top: 20px; padding-bottom: 10px; border-top: 1px solid var(--border); text-align: center; color: var(--secondary); font-size: 14px; font-weight: 500; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <div><h1>방갤 갤 대회 목록 대시보드</h1></div>
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
    <div id="eventGrid" class="grid"></div>
    <footer>made by Bangbung Kim</footer>
</div>
<script>
    const events = {events_json};

    function updateClock() {{
        const now = new Date();
        const options = {{ year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }};
        document.getElementById('clock').innerText = now.toLocaleString('ko-KR', options);
    }}

    function getRemainingTime(endDateStr) {{
        if (!endDateStr) return {{ status: 'ended', text: '날짜 미정/종료' }};
        
        const now = new Date();
        const end = new Date(endDateStr.replace(' ', 'T'));
        const diff = end - now;

        if (isNaN(diff) || diff < 0) {{
            return {{ status: 'ended', text: '종료됨' }};
        }}

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

        let text = '';
        if (days > 0) text += days + '일 ';
        text += hours + '시간 ';
        text += minutes + '분 남음';

        let status = 'safe';
        if (days < 3) status = 'critical';
        else if (days < 7) status = 'warning';
        else if (days < 30) status = 'notice';
        
        return {{ status: status, text: text, diff: diff }};
    }}

    function renderEvents() {{
        const grid = document.getElementById('eventGrid');
        const sortType = document.getElementById('sortSelect').value;
        grid.innerHTML = '';

        const sortedEvents = [...events].sort((a, b) => {{
            if (sortType === 'endingSoon') {{
                if (!a.js_end_date) return 1; 
                if (!b.js_end_date) return -1;
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
                    <div class="organizer"><span>주최: ${{evt.주최자_닉}} (${{evt.주최자_식별코드}})</span></div>
                </div>
                <div class="card-body">
                    <div class="dates">
                        <div class="date-row"><span>시작:</span> <span>${{evt.시작일}}</span></div>
                        <div class="date-row"><span>종료:</span> <span>${{evt.종료일}}</span></div>
                    </div>
                    <div class="timer-badge ${{remaining.status}}">${{remaining.text}}</div>
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
    print(f"알림: {OUTPUT_FILE} 생성 완료.")

if __name__ == "__main__":
    process_events()