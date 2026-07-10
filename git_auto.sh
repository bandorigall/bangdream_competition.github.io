#!/bin/bash
# 빌드(venv + python -m main) -> 커밋 -> pull -> push -> 배포 완료 대기 -> 브라우저 열기
# 사용법: ./git_auto.sh "커밋메시지"   (생략 시 자동 생성)

set +H  # '!' 히스토리 확장 비활성화

# 0. 스크립트 자신의 폴더로 이동 (어디서 실행하든 동작)
cd "$(dirname "$0")" || exit 1

# 1. 페이지 빌드 (main.bat 통합: venv 활성화 후 python -m main)
#    main.bat 은 D:\venv_dev 를 활성화하므로, 그 venv 의 파이썬을 직접 사용한다.
PYTHON="D:/venv_dev/Scripts/python.exe"
[ -x "$PYTHON" ] || PYTHON="python"
echo "[+] Building (python -m main)..."
"$PYTHON" -m main
if [ $? -ne 0 ]; then
    echo ""
    echo " [ERROR] 빌드 실패. main.py 또는 venv 경로를 확인하세요."
    read -p "[?] 창을 닫으려면 Enter를 누르세요..." _
    exit 1
fi

# 2. 변경사항 추가
echo "[+] Adding changes..."
git add .

# 3. 커밋 (메시지는 실행 시 인자로 받거나 기본값 사용)
COMMIT_MSG=${1:-"Auto commit - $(date '+%Y-%m-%d %H:%M:%S')"}
if git diff --cached --quiet; then
    echo "[i] 커밋할 변경사항이 없습니다. 커밋을 건너뜁니다."
else
    echo "[+] Committing with message: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
fi

# 4. Pull (원격 저장소 변경사항 가져오기)
#    --no-edit: 머지 커밋 에디터(vim) 멈춤 방지 / --no-rebase: pull 전략 명시
echo "[+] Pulling from remote..."
git pull --no-rebase --no-edit
if [ $? -ne 0 ]; then
    echo ""
    echo "###################################################"
    echo " [!!!] 에러 발생: 머지 충돌(Conflict)이 감지되었습니다."
    echo " 직접 충돌을 해결한 뒤 다시 실행해주세요."
    echo "###################################################"
    read -p "[?] 창을 닫으려면 Enter를 누르세요..." _
    exit 1
fi

# 5. Push
echo "[+] Pushing to remote..."
git push
if [ $? -ne 0 ]; then
    echo ""
    echo " [!!!] 에러 발생: Push 실패! (권한 문제 또는 원격 설정 확인)"
    read -p "[?] 창을 닫으려면 Enter를 누르세요..." _
    exit 1
fi

echo ""
echo "[OK] 빌드 + 커밋 + 푸시 완료!"

# push_all.sh 등에서 SKIP_DEPLOY_WAIT=1 로 부르면 배포 대기/브라우저 열기 없이 즉시 종료
[ -n "$SKIP_DEPLOY_WAIT" ] && exit 0

# 6. 이 커밋의 GitHub Pages 배포가 끝날 때까지 기다린 뒤 브라우저 열기
URL="https://bandorigall.github.io/bangdream_competition.github.io/"
REPO="bandorigall/bangdream_competition.github.io"
PUSHED_SHA="$(git rev-parse HEAD)"

if command -v gh >/dev/null 2>&1; then
    echo "[+] Waiting for GitHub Pages to deploy commit ${PUSHED_SHA:0:7} ..."
    MAX_WAIT=300   # seconds
    INTERVAL=5
    WAITED=0
    DEPLOYED=0
    # deployments API(github-pages 환경)로 추적. 레거시 pages/builds 엔드포인트는
    # 새 배포를 제때 반영하지 못해 무한 대기가 발생하므로 사용하지 않는다.
    while [ "$WAITED" -lt "$MAX_WAIT" ]; do
        DEPLOY_ID="$(gh api "repos/$REPO/deployments?sha=$PUSHED_SHA&environment=github-pages&per_page=1" \
                        --jq '.[0].id' 2>/dev/null)"
        if [ -n "$DEPLOY_ID" ] && [ "$DEPLOY_ID" != "null" ]; then
            STATE="$(gh api "repos/$REPO/deployments/$DEPLOY_ID/statuses?per_page=1" \
                        --jq '.[0].state' 2>/dev/null)"
            case "$STATE" in
                success)
                    echo "[OK] Pages deploy completed for ${PUSHED_SHA:0:7}."
                    DEPLOYED=1
                    break
                    ;;
                error|failure)
                    echo "[ERROR] Pages deploy $STATE for ${PUSHED_SHA:0:7}. Opening site anyway."
                    break
                    ;;
            esac
        else
            STATE="pending"
        fi
        printf '    ... state=%s (%ss elapsed)\r' "${STATE:-pending}" "$WAITED"
        sleep "$INTERVAL"
        WAITED=$((WAITED + INTERVAL))
    done
    echo ""
    if [ "$DEPLOYED" -ne 1 ] && [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo "[i] Timed out waiting for deploy (${MAX_WAIT}s). Opening site anyway."
    fi
else
    echo "[i] 'gh' not found; cannot track deploy status. Opening site directly."
fi

echo "[+] Opening $URL ..."
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)   # Windows (Git Bash / MSYS / Cygwin)
        powershell.exe -NoProfile -Command "Start-Process '$URL'" \
            || echo "[i] 브라우저 자동 실행 실패. 수동으로 여세요: $URL"
        ;;
    Linux*)                 # Linux
        xdg-open "$URL" >/dev/null 2>&1 \
            || echo "[i] 브라우저 자동 실행 실패. 수동으로 여세요: $URL"
        ;;
    Darwin*)                # macOS
        open "$URL" \
            || echo "[i] 브라우저 자동 실행 실패. 수동으로 여세요: $URL"
        ;;
    *)
        echo "[i] 알 수 없는 OS. 수동으로 여세요: $URL"
        ;;
esac

read -p "[?] 창을 닫으려면 Enter를 누르세요..." _
exit 0
