"""
StepAnimator: reproductor ▶ ⏸ ■ para animaciones por frame. No usa slider.
El usuario da una función step(t ∈ [0,1]); StepAnimator llama a step() en
cada tick y refresca. La barra de progreso es indicadora, no interactiva.
"""

from __future__ import annotations

from typing import Callable, Optional

import ttkbootstrap as ttk


class StepAnimator(ttk.Frame):
    """Footer con botones Play/Pause/Stop y barra de progreso."""

    def __init__(
        self,
        parent,
        step_fn: Callable[[float], None],
        duration_ms: int = 2500,
        fps: int = 30,
        on_start: Optional[Callable[[], None]] = None,
        on_end: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._step_fn = step_fn
        self._duration_ms = duration_ms
        self._frame_ms = max(16, int(1000 / fps))
        self._on_start = on_start
        self._on_end = on_end

        self._elapsed = 0
        self._running = False
        self._after_id: Optional[str] = None

        self.btn_play = ttk.Button(self, text="▶", width=3, bootstyle="success",
                                   command=self.play)
        self.btn_pause = ttk.Button(self, text="⏸", width=3, bootstyle="warning",
                                    command=self.pause)
        self.btn_stop = ttk.Button(self, text="■", width=3, bootstyle="danger",
                                   command=self.stop)
        self.btn_play.pack(side="left", padx=(0, 4))
        self.btn_pause.pack(side="left", padx=4)
        self.btn_stop.pack(side="left", padx=4)

        self.progress = ttk.Progressbar(self, mode="determinate",
                                         bootstyle="info-striped",
                                         maximum=1.0, value=0.0)
        self.progress.pack(side="left", fill="x", expand=True, padx=(12, 0))

    def set_step_fn(self, fn: Callable[[float], None]) -> None:
        self._step_fn = fn

    def set_duration(self, ms: int) -> None:
        self._duration_ms = max(100, int(ms))

    # ---------- control ----------
    def play(self) -> None:
        if self._running:
            return
        if self._elapsed >= self._duration_ms:
            self._elapsed = 0
        self._running = True
        if self._on_start:
            self._on_start()
        self._tick()

    def pause(self) -> None:
        self._running = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def stop(self) -> None:
        self.pause()
        self._elapsed = 0
        try:
            self.progress.configure(value=0.0)
        except Exception:
            pass
        try:
            self._step_fn(0.0)
        except Exception:
            pass

    def _tick(self) -> None:
        if not self._running:
            return
        t = min(1.0, self._elapsed / self._duration_ms)
        try:
            self._step_fn(t)
        except Exception:
            self._running = False
            return
        try:
            self.progress.configure(value=t)
        except Exception:
            pass
        if t >= 1.0:
            self._running = False
            if self._on_end:
                self._on_end()
            return
        self._elapsed += self._frame_ms
        self._after_id = self.after(self._frame_ms, self._tick)
