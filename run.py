import argparse
import base64
import io
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import mss
from PIL import Image
from openai import OpenAI

COMPUTER_USE_TOOL_SPEC: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "computer_use",
        "description": (
            "Use a mouse and keyboard to interact with a computer, and take screenshots.\n"
            "* This is an interface to a desktop GUI. You do not have access to a terminal or "
            "applications menu. You must click on desktop icons to start applications.\n"
            "* Some applications may take time to start or process actions, so you may need to wait "
            "and take successive screenshots to see the results of your actions. E.g. if you click on "
            "Firefox and a window doesn't open, try wait and taking another screenshot.\n"
            f"* The screen's resolution is dynamically detected from the host system.\n"
            "* Whenever you intend to move the cursor to click on an element like an icon, you should consult "
            "a screenshot to determine the coordinates of the element before moving the cursor.\n"
            "* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element."
        ),
        "parameters": {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "key",
                        "type",
                        "mouse_move",
                        "left_click",
                        "left_click_drag",
                        "right_click",
                        "middle_click",
                        "double_click",
                        "triple_click",
                        "scroll",
                        "hscroll",
                        "wait",
                        "terminate",
                        "answer",
                    ],
                    "description": "The action to perform.",
                },
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keys used with action=key.",
                },
                "text": {
                    "type": "string",
                    "description": "Text for action=type or action=answer.",
                },
                "coordinate": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Target coordinate [x, y] for mouse actions.",
                },
                "pixels": {
                    "type": "number",
                    "description": "Scroll amount for action=scroll or action=hscroll.",
                },
                "time": {
                    "type": "number",
                    "description": "Seconds to wait for action=wait.",
                },
                "status": {
                    "type": "string",
                    "enum": ["success", "failure"],
                    "description": "Task status for action=terminate.",
                },
            },
        },
    },
}

SYSTEM_PROMPT = """You are an automation agent with direct access to a GUI computer.
- Be precise and avoid unnecessary movements.
- Always inspect the most recent screenshot before clicking.
- If an application needs time to load, wait before taking more actions.
- You must finish by calling action=answer with the final response and action=terminate with success/failure."""


_pyautogui = None


def _ensure_display() -> None:
    if sys.platform.startswith("linux") and "DISPLAY" not in os.environ:
        msg = (
            "DISPLAY 환경 변수가 설정되지 않았습니다. pyautogui를 사용하려면 X11 또는 "
            "가상 디스플레이(Xvfb 등)가 필요합니다. 예: `sudo apt install xvfb && "
            "xvfb-run -s \"-screen 0 1920x1080x24\" uv run python run.py ...`"
        )
        raise RuntimeError(msg)


def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        _ensure_display()
        import pyautogui  # type: ignore

        pyautogui.FAILSAFE = False
        _pyautogui = pyautogui
    return _pyautogui


def _now_ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _ensure_xy(coordinate: Optional[List[float]]) -> List[int]:
    if not coordinate or len(coordinate) != 2:
        raise ValueError("coordinate=[x, y] is required for this action.")
    return [int(coordinate[0]), int(coordinate[1])]


def _maybe_int(value: Optional[float], default: int = 0) -> int:
    return int(value) if value is not None else default


@dataclass
class ToolResult:
    payload: Dict[str, Any]

    def as_json(self) -> str:
        return json.dumps(self.payload, ensure_ascii=False)


class ComputerUseTool:
    def __init__(
        self,
        screenshot_dir: Path,
        monitor_index: int = 1,
        mouse_move_duration: float = 0.0,
        drag_duration: float = 0.15,
    ) -> None:
        self.screenshot_dir = screenshot_dir
        self.monitor_index = monitor_index
        self.mouse_move_duration = mouse_move_duration
        self.drag_duration = drag_duration
        self.pg = _get_pyautogui()
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def call(self, params: Dict[str, Any]) -> ToolResult:
        action = params["action"]
        handler = {
            "mouse_move": self._mouse_move,
            "left_click": self._left_click,
            "right_click": self._right_click,
            "middle_click": self._middle_click,
            "double_click": self._double_click,
            "triple_click": self._triple_click,
            "left_click_drag": self._left_click_drag,
            "scroll": self._scroll,
            "hscroll": self._hscroll,
            "type": self._type,
            "key": self._key,
            "wait": self._wait,
            "answer": self._answer,
            "terminate": self._terminate,
        }.get(action)

        if handler is None:
            raise ValueError(f"Unsupported action: {action}")

        result = handler(params)
        if action in {"answer", "terminate"}:
            return ToolResult(payload=result)
        return ToolResult(payload=self._attach_screenshot(result))

    def _mouse_move(self, params: Dict[str, Any]) -> Dict[str, Any]:
        x, y = _ensure_xy(params.get("coordinate"))
        self.pg.moveTo(x, y, duration=self.mouse_move_duration)
        return {"status": "ok", "detail": f"Moved to ({x}, {y})."}

    def _left_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        coord = params.get("coordinate")
        if coord:
            x, y = _ensure_xy(coord)
            self.pg.click(x, y, button="left")
            detail = f"Left click at ({x}, {y})."
        else:
            self.pg.click(button="left")
            detail = "Left click at current cursor."
        return {"status": "ok", "detail": detail}

    def _right_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        coord = params.get("coordinate")
        if coord:
            x, y = _ensure_xy(coord)
            self.pg.click(x, y, button="right")
            detail = f"Right click at ({x}, {y})."
        else:
            self.pg.click(button="right")
            detail = "Right click at current cursor."
        return {"status": "ok", "detail": detail}

    def _middle_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        coord = params.get("coordinate")
        if coord:
            x, y = _ensure_xy(coord)
            self.pg.click(x, y, button="middle")
            detail = f"Middle click at ({x}, {y})."
        else:
            self.pg.click(button="middle")
            detail = "Middle click at current cursor."
        return {"status": "ok", "detail": detail}

    def _double_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        x, y = _ensure_xy(params.get("coordinate"))
        self.pg.doubleClick(x, y)
        return {"status": "ok", "detail": f"Double click at ({x}, {y})."}

    def _triple_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        x, y = _ensure_xy(params.get("coordinate"))
        self.pg.tripleClick(x, y)
        return {"status": "ok", "detail": f"Triple click at ({x}, {y})."}

    def _left_click_drag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        x, y = _ensure_xy(params.get("coordinate"))
        self.pg.mouseDown()
        self.pg.dragTo(x, y, duration=self.drag_duration, button="left")
        self.pg.mouseUp()
        return {"status": "ok", "detail": f"Drag to ({x}, {y})."}

    def _scroll(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pixels = _maybe_int(params.get("pixels"))
        self.pg.scroll(pixels)
        return {"status": "ok", "detail": f"Scroll {pixels} vertically."}

    def _hscroll(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pixels = _maybe_int(params.get("pixels"))
        self.pg.hscroll(pixels)
        return {"status": "ok", "detail": f"Scroll {pixels} horizontally."}

    def _type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("text")
        if text is None:
            raise ValueError("text is required for action=type.")
        self.pg.typewrite(text, interval=0.01)
        return {"status": "ok", "detail": f'Typed "{text[:50]}".'}

    def _key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        keys = params.get("keys") or []
        if not keys:
            raise ValueError("keys is required for action=key.")
        for key in keys:
            self.pg.keyDown(key)
        for key in reversed(keys):
            self.pg.keyUp(key)
        return {"status": "ok", "detail": f"Pressed keys {keys}."}

    def _wait(self, params: Dict[str, Any]) -> Dict[str, Any]:
        duration = params.get("time")
        if duration is None:
            raise ValueError("time is required for action=wait.")
        time.sleep(float(duration))
        return {"status": "ok", "detail": f"Waited {duration} seconds."}

    def _answer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("text") or ""
        return {"status": "answer", "text": text}

    def _terminate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        status = params.get("status")
        if status not in {"success", "failure"}:
            raise ValueError("status must be success or failure for action=terminate.")
        return {"status": "terminate", "result": status}

    def _attach_screenshot(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with mss.mss() as sct:
            monitor = sct.monitors[self.monitor_index]
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)

        path = self.screenshot_dir / f"{_now_ts()}.png"
        img.save(path)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

        cursor = self.pg.position()
        payload.update(
            {
                "screenshot": f"data:image/png;base64,{encoded}",
                "screenshot_path": str(path),
                "cursor": {"x": cursor.x, "y": cursor.y},
                "display": {
                    "width": monitor["width"],
                    "height": monitor["height"],
                },
            }
        )
        return payload


class ComputerUseAgent:
    def __init__(
        self,
        client: OpenAI,
        tool: ComputerUseTool,
        model: str,
        task: str,
        temperature: float,
        max_turns: int,
    ) -> None:
        self.client = client
        self.tool = tool
        self.model = model
        self.task = task
        self.temperature = temperature
        self.max_turns = max_turns
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]
        self.final_answer: Optional[str] = None
        self.terminated: Optional[str] = None

    def run(self) -> None:
        for step in range(1, self.max_turns + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=[COMPUTER_USE_TOOL_SPEC],
                temperature=self.temperature,
            )
            message = response.choices[0].message
            self.messages.append(message)

            tool_calls = message.tool_calls or []
            if not tool_calls:
                content = message.content or ""
                print(f"[Assistant] {content}")
                self.final_answer = content
                break

            for tool_call in tool_calls:
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = self.tool.call(arguments)
                payload = result.payload

                if payload.get("status") == "answer":
                    self.final_answer = payload.get("text", "")
                    print(f"[Agent Answer] {self.final_answer}")

                if payload.get("status") == "terminate":
                    self.terminated = payload.get("result")
                    print(f"[Terminate] status={self.terminated}")

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result.as_json(),
                    }
                )

            if self.terminated:
                break


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal computer-use agent driver.")
    parser.add_argument("--model", type=str, default="Qwen/Qwen3-VL-30B-A3B-Instruct")
    parser.add_argument("--task", type=str, required=False, default="Open a browser and search for the weather.")
    parser.add_argument("--api-key", type=str, default="EMPTY")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000/v1")
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--max-turns", type=int, default=200)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--screenshot-dir", type=Path, default=Path("./screenshots"))
    parser.add_argument("--monitor-index", type=int, default=1)
    parser.add_argument("--mouse-move-duration", type=float, default=0.0)
    parser.add_argument("--drag-duration", type=float, default=0.15)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    client = OpenAI(
        api_key=args.api_key,
        base_url=args.base_url,
        timeout=args.timeout,
    )

    tool = ComputerUseTool(
        screenshot_dir=args.screenshot_dir,
        monitor_index=args.monitor_index,
        mouse_move_duration=args.mouse_move_duration,
        drag_duration=args.drag_duration,
    )

    agent = ComputerUseAgent(
        client=client,
        tool=tool,
        model=args.model,
        task=args.task,
        temperature=args.temperature,
        max_turns=args.max_turns,
    )
    agent.run()

    if agent.final_answer:
        print(f"[Final Answer] {agent.final_answer}")
    if agent.terminated:
        print(f"[Task Status] {agent.terminated}")


if __name__ == "__main__":
    main()