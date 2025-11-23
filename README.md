# Qwen3 Computer Use

Minimal한 Qwen3 GUI 에이전트 드라이버입니다. vLLM(OpenAI 호환) 엔드포인트에 `computer_use` 도구를 노출하고, 로컬 머신의 마우스·키보드·스크린샷 제어를 `pyautogui`/`mss`로 직접 수행합니다.

## 요구 사항
- Python 3.10 이상
- GUI 제어 권한(X11/Wayland/VNC 등)과 물리 디스플레이/가상 디스플레이
- Qwen3 계열 모델을 서비스 중인 OpenAI 호환 서버(예: `http://localhost:8000/v1`)

## 설치
```bash
cd /home/robin/qwen3_computer_use
uv sync
```

## 실행
```bash
uv run python run.py \
  --model "Qwen/Qwen3-VL-30B-A3B-Instruct" \
  --task "브라우저를 열고 ACL 2026 템플릿을 다운로드해줘" \
  --base-url "http://localhost:8000/v1" \
  --api-key "EMPTY" \
  --screenshot-dir /tmp/qwen3-shots
```

주요 옵션:
- `--max-turns`: 모델 호출 최대 횟수(기본 200)
- `--monitor-index`: `mss` 모니터 인덱스(기본 1, 전체 모니터 목록은 `mss().monitors`)
- `--mouse-move-duration` / `--drag-duration`: 포인터 이동/드래그 시간

실행 중 에이전트가 수행한 모든 물리 액션은 자동으로 스크린샷(Base64)·커서 좌표와 함께 모델에게 전달되며, 모델은 반드시 `answer` → `terminate` 순으로 작업을 종료해야 합니다.

## 참고
- `pyautogui.FAILSAFE`가 비활성화되어 있으므로 테스트는 반드시 격리된 VM/컨테이너에서 수행하는 것이 안전합니다.
- 추가적인 로깅이나 상태 관리가 필요하면 `ComputerUseTool` 또는 `ComputerUseAgent` 클래스를 확장하세요.

