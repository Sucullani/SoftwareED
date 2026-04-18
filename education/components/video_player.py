"""
VideoPlayer: reproductor de MP4 embebido en tkinter para los módulos
educativos. Usa `tkvideoplayer` si está instalado; si no, degrada a un
placeholder con mensaje de instalación.
"""

from __future__ import annotations

import os
from typing import Optional

import tkinter as tk
import ttkbootstrap as ttk

try:
    from tkvideoplayer import TkinterVideo  # type: ignore
    _TKVIDEO_OK = True
except Exception:
    TkinterVideo = None  # type: ignore
    _TKVIDEO_OK = False


class VideoPlayer(ttk.Frame):
    """Widget con video + controles Play/Pause/Stop/Seek.

    Si tkvideoplayer no está disponible o el archivo no existe, muestra un
    mensaje amable en lugar de romper el módulo.
    """

    def __init__(
        self,
        parent,
        source: Optional[str] = None,
        autoplay: bool = False,
        loop: bool = False,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._source = source
        self._loop = loop

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._body = ttk.Frame(self)
        self._body.grid(row=0, column=0, sticky="nsew")
        self._body.columnconfigure(0, weight=1)
        self._body.rowconfigure(0, weight=1)

        self._controls = ttk.Frame(self)
        self._controls.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        self._video = None
        self._duration = 0.0
        self._placeholder = None
        self._build()

        if autoplay and self._video is not None:
            self.after(120, self.play)

    # ---------- construcción ----------
    def _build(self) -> None:
        if not _TKVIDEO_OK:
            self._placeholder = ttk.Label(
                self._body, justify="center", bootstyle="warning",
                text=(
                    "tkvideoplayer no está instalado.\n"
                    "Ejecute:  pip install tkvideoplayer\n"
                    "y reabra este módulo."
                ),
                font=("Segoe UI", 10),
            )
            self._placeholder.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            self._build_controls(enabled=False)
            return

        if self._source is None or not os.path.exists(self._source):
            path_info = self._source if self._source else "(sin ruta)"
            self._placeholder = ttk.Label(
                self._body, justify="center", bootstyle="info",
                text=(
                    "Video no encontrado.\n"
                    f"Esperado en: {path_info}\n\n"
                    "Coloque el archivo .mp4 en esa ruta y reabra el módulo."
                ),
                font=("Segoe UI", 10),
            )
            self._placeholder.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            self._build_controls(enabled=False)
            return

        self._video = TkinterVideo(master=self._body, scaled=True)
        self._video.grid(row=0, column=0, sticky="nsew")
        self._video.load(self._source)
        self._video.bind("<<Duration>>", self._on_duration)
        self._video.bind("<<SecondChanged>>", self._on_second_changed)
        self._video.bind("<<Ended>>", self._on_ended)

        self._build_controls(enabled=True)

    def _build_controls(self, enabled: bool) -> None:
        for w in self._controls.winfo_children():
            w.destroy()

        self._btn_play = ttk.Button(
            self._controls, text="▶", width=3, bootstyle="success",
            command=self.play, state=("normal" if enabled else "disabled"),
        )
        self._btn_play.pack(side="left", padx=2)

        self._btn_pause = ttk.Button(
            self._controls, text="⏸", width=3, bootstyle="warning",
            command=self.pause, state=("normal" if enabled else "disabled"),
        )
        self._btn_pause.pack(side="left", padx=2)

        self._btn_stop = ttk.Button(
            self._controls, text="■", width=3, bootstyle="danger",
            command=self.stop, state=("normal" if enabled else "disabled"),
        )
        self._btn_stop.pack(side="left", padx=2)

        self._scale_var = tk.DoubleVar(value=0.0)
        self._scale = ttk.Scale(
            self._controls, from_=0, to=100, orient="horizontal",
            variable=self._scale_var, bootstyle="info",
            command=self._on_seek,
        )
        self._scale.pack(side="left", fill="x", expand=True, padx=8)
        if not enabled:
            self._scale.state(["disabled"])

        self._lbl_time = ttk.Label(self._controls, text="0:00 / 0:00",
                                     font=("Consolas", 9))
        self._lbl_time.pack(side="left", padx=4)

    # ---------- API pública ----------
    def play(self) -> None:
        if self._video is not None:
            try:
                self._video.play()
            except Exception:
                pass

    def pause(self) -> None:
        if self._video is not None:
            try:
                self._video.pause()
            except Exception:
                pass

    def stop(self) -> None:
        if self._video is not None:
            try:
                self._video.stop()
                if self._source:
                    self._video.load(self._source)
                self._scale_var.set(0)
                self._update_time_label(0.0)
            except Exception:
                pass

    def seek(self, seconds: float) -> None:
        if self._video is not None:
            try:
                self._video.seek(int(seconds))
            except Exception:
                pass

    # ---------- eventos tkvideoplayer ----------
    def _on_duration(self, _event) -> None:
        if self._video is None:
            return
        try:
            self._duration = float(self._video.video_info()["duration"])
            self._scale.configure(from_=0, to=max(1.0, self._duration))
        except Exception:
            self._duration = 0.0

    def _on_second_changed(self, _event) -> None:
        if self._video is None:
            return
        try:
            cur = float(self._video.current_duration())
            self._scale_var.set(cur)
            self._update_time_label(cur)
        except Exception:
            pass

    def _on_ended(self, _event) -> None:
        if self._loop and self._video is not None:
            try:
                self._video.load(self._source)
                self._video.play()
            except Exception:
                pass

    def _on_seek(self, value) -> None:
        try:
            self.seek(float(value))
        except Exception:
            pass

    def _update_time_label(self, cur: float) -> None:
        def fmt(s: float) -> str:
            s = max(0, int(s))
            return f"{s // 60}:{s % 60:02d}"
        self._lbl_time.configure(
            text=f"{fmt(cur)} / {fmt(self._duration)}"
        )
