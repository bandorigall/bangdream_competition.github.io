#!/bin/bash
# (Linux) 빌드(python3 -m main) -> 커밋 -> pull -> push -> 배포 완료 대기 -> 브라우저 열기
# 사용법: ./git_auto_linux.sh "커밋메시지"   (생략 시 자동 생성)

cd "$(dirname "$0")" || exit 1

git config user.name "bandorigall"
git config user.email "bandorigall@users.noreply.github.com"

# 1. 페이지 빌드 (main.bat 통합: python3 -m main)
PYTHON="$(command -v python3 || command -v python)"
echo "[+] Building (python -m main)..."
"$PYTHON" -m main
if [ $? -ne 0 ]; then
    echo ""
    echo " [ERROR] 빌드 실패. main.py 를 확인하세요."
    exit 1
fi

echo "[+] Adding changes..."
git add .

COMMIT_MSG=${1:-"Auto commit - $(date '+%Y-%m-%d %H:%M:%S')"}
if git diff --cached --quiet; then
    echo "[i] 커밋할 변경사항이 없습니다. 커밋을 건너뜁니다."
else
    echo "[+] Committing with message: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
fi

echo "[+] Pulling from remote..."
# --no-edit: 머지 커밋 에디터 멈춤 방지 / --no-rebase: pull 전략 명시
git pull --no-rebase --no-edit
if [ $? -ne 0 ]; then
    echo ""
    echo "###################################################"
    echo " [!!!] 에러 발생: 머지 충돌(Conflict)이 감지되었습니다."
    echo " 직접 충돌을 해결한 뒤 다시 실행해주세요."
    echo "###################################################"
    exit 1
fi

echo "[+] Pushing to remote..."
TOKEN=$(cat ~/dev/gittoken.txt | tr -d '[:space:]')
git remote set-url origin "https://bandorigall:${TOKEN}@github.com/bandorigall/bangdream_competition.github.io.git"
git push
if [ $? -ne 0 ]; then
    echo ""
    echo " [!!!] 에러 발생: Push 실패! (권한 문제 또는 원격 설정 확인)"
    exit 1
fi

echo ""
echo "[OK] 빌드 + 커밋 + 푸시 완료!"

# 배포 완료 대기 후 브라우저 열기
URL="https://bandorigall.github.io/bangdream_competition.github.io/"
REPO="bandorigall/bangdream_competition.github.io"
PUSHED_SHA="$(git rev-parse HEAD)"
API="https://api.github.com"

# deployments API(github-pages 환경)로 추적. gh 가 있으면 gh, 없으면 토큰으로 curl.
gh_get() {  # $1 = API path (repos/... 이후)
    if command -v gh >/dev/null 2>&1; then
        gh api "$1" 2>/dev/null
    else
        curl -s -H "Authorization: Bearer $TOKEN" \
             -H "Accept: application/vnd.github+json" "$API/$1"
    fi
}

echo "[+] Waiting for GitHub Pages to deploy commit ${PUSHED_SHA:0:7} ..."
MAX_WAIT=300   # seconds
INTERVAL=5
WAITED=0
DEPLOYED=0
while [ "$WAITED" -lt "$MAX_WAIT" ]; do
    DJSON="$(gh_get "repos/$REPO/deployments?sha=$PUSHED_SHA&environment=github-pages&per_page=1")"
    DEPLOY_ID="$(printf '%s' "$DJSON" | sed -n 's/.*"id":[ ]*\([0-9]*\).*/\1/p' | head -1)"
    if [ -n "$DEPLOY_ID" ]; then
        SJSON="$(gh_get "repos/$REPO/deployments/$DEPLOY_ID/statuses?per_page=1")"
        STATE="$(printf '%s' "$SJSON" | sed -n 's/.*"state":[ ]*"\([^"]*\)".*/\1/p' | head -1)"
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

echo "[+] Opening $URL ..."
xdg-open "$URL" >/dev/null 2>&1 \
    || echo "[i] 브라우저 자동 실행 실패. 수동으로 여세요: $URL"

exit 0
