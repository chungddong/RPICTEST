from __future__ import annotations

import os
import secrets
import subprocess
import threading
from collections import deque


class TerminalSession:
    def __init__(self) -> None:
        self.id = secrets.token_hex(8)
        self.offset = 0
        self.buffer = deque[str]()
        self.lock = threading.Lock()
        self.closed = False

        if os.name == "nt":
            self.process = subprocess.Popen(
                ["cmd.exe"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                bufsize=0,
            )
            self.reader = threading.Thread(target=self._read_pipe, daemon=True)
        else:
            import pty

            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd
            self.process = subprocess.Popen(
                [os.environ.get("SHELL", "/bin/bash")],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                text=False,
                close_fds=True,
            )
            os.close(slave_fd)
            self.reader = threading.Thread(target=self._read_pty, daemon=True)

        self.reader.start()

    def _append(self, text: str) -> None:
        if not text:
            return
        with self.lock:
            self.buffer.append(text)
            self.offset += len(text)
            while len(self.buffer) > 500:
                self.buffer.popleft()

    def _read_pipe(self) -> None:
        assert self.process.stdout is not None
        while self.process.poll() is None:
            chunk = self.process.stdout.read(1024)
            if not chunk:
                break
            self._append(chunk.decode(errors="replace"))

    def _read_pty(self) -> None:
        while self.process.poll() is None:
            try:
                data = os.read(self.master_fd, 1024)
            except OSError:
                break
            self._append(data.decode(errors="replace"))

    def write(self, content: str) -> None:
        if self.closed:
            return

        if os.name == "nt":
            assert self.process.stdin is not None
            self.process.stdin.write(content.encode())
            self.process.stdin.flush()
            return

        os.write(self.master_fd, content.encode())

    def read(self, offset: int) -> dict[str, object]:
        with self.lock:
            current = "".join(self.buffer)
            start = max(0, offset - max(self.offset - len(current), 0))
            chunk = current[start:]
            next_offset = self.offset
        return {
            "session_id": self.id,
            "output": chunk,
            "offset": next_offset,
            "alive": self.process.poll() is None,
        }

    def close(self) -> None:
        self.closed = True
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=2)
        if self.process.stdin is not None:
            self.process.stdin.close()
        if self.process.stdout is not None:
            self.process.stdout.close()


class TerminalManager:
    def __init__(self) -> None:
        self.sessions: dict[str, TerminalSession] = {}

    def create_session(self) -> dict[str, object]:
        session = TerminalSession()
        self.sessions[session.id] = session
        return {"session_id": session.id}

    def write(self, session_id: str, content: str) -> None:
        session = self.sessions[session_id]
        session.write(content)

    def read(self, session_id: str, offset: int) -> dict[str, object]:
        session = self.sessions[session_id]
        return session.read(offset)

    def close_all(self) -> None:
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()
