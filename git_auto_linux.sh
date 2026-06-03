#!/bin/bash
git config user.name "bandorigall"
git config user.email "bandorigall@users.noreply.github.com"

echo "[+] Adding changes..."
git add .

COMMIT_MSG=${1:-"Auto commit - $(date '+%Y-%m-%d %H:%M:%S')"}
echo "[+] Committing with message: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

echo "[+] Pulling from remote..."
git pull
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
echo "[OK] 모든 작업이 성공적으로 완료되었습니다!"
