"""
WebpPlayer: reproductor lightweight de WebP animado para tkinter, basado
solo en Pillow (sin PyAV/FFmpeg). Drop-in replacement de TkinterVideo
para los diálogos educativos del menú Modelo.

API mínima compatible con el patrón previo:

    player = WebpPlayer(parent, scaled=True, background="#1a1a1a")
    player.pack(fill=BOTH, expand=YES)
    player.load("resources/videos/q4_q9_transition.webp")
    player.play()
    ...
    player.stop()  # cleanup automático en <Destroy>

Características:
  · Auto-loop seamless (al terminar vuelve al frame 0 sin pausa).
  · Escalado a tamaño del widget cuando scaled=True (preserva aspect).
  · Sin controles visibles.
  · Decodificación on-the-fly por frame (sin cache → bajo footprint RAM).
  · Sin threads — usa `after()` de tkinter para el timing.

Por qué WebP en vez de MP4: evita la dependencia PyAV (~30 MB de FFmpeg
DLLs en el instalador PyInstaller) sin sacrificar mucho de calidad para
clips cortos. Pillow ya está en las deps del proyecto.
"""

from __future__ import annotations

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, YES

from PIL import Image, ImageTk


class WebpPlayer(ttk.Frame):
    """Reproductor de WebP animado en loop seamless."""

    def __init__(
        self,
        parent,
        *,
        scaled: bool = True,
        background: str = "#1a1a1a",
        **kw,
    ):
        super().__init__(parent, **kw)
        self._scaled = scaled
        self._bg = background

        self._label = tk.Label(
            self, bg=background, bd=0, highlightthickness=0,
        )
        self._label.pack(fill=BOTH, expand=YES)

        self._img: Image.Image | None = None      # PIL.Image fuente animada
        self._n_frames: int = 0
        self._current_frame: int = 0
        self._frame_durations: list[int] = []     # ms por frame
        self._photo: ImageTk.PhotoImage | None = None   # ref anti-GC
        self._after_id: str | None = None
        self._playing: bool = False

        # Callback opcional invocado tras pintar cada frame:
        #     on_frame_change(current_frame, current_ms, total_ms)
        # Útil para sincronizar un scrubber externo. None por defecto.
        self.on_frame_change = None

        self.bind("<Destroy>", self._on_destroy)

    # ─── API pública ────────────────────────────────────────────────────
    def load(self, path: str) -> None:
        """Carga un WebP animado (o estático) y deja el widget listo para
        play(). Si ya había uno cargado, lo reemplaza."""
        self.stop()
        img = Image.open(path)
        n_frames = getattr(img, "n_frames", 1)
        durations: list[int] = []
        for i in range(n_frames):
            img.seek(i)
            # `duration` viene en ms. Algunos encoders (notablemente el
            # muxer libwebp de ffmpeg) escriben 0 en lugar de ausente —
            # tratamos 0 como missing y usamos 45 ms (~22 fps) por defecto.
            d = int(img.info.get("duration", 0) or 0)
            durations.append(d if d > 0 else 45)
        img.seek(0)

        self._img = img
        self._n_frames = n_frames
        self._frame_durations = durations
        self._current_frame = 0

        # Pintar el primer frame inmediatamente para que el widget no se
        # vea vacío hasta el primer tick.
        self._render_current_frame()

    def play(self) -> None:
        """Inicia la reproducción en loop. Idempotente."""
        if self._img is None or self._playing:
            return
        self._playing = True
        self._schedule_next()

    def pause(self) -> None:
        """Pausa la reproducción manteniendo la posición actual."""
        self.stop()

    def stop(self) -> None:
        """Detiene la reproducción y cancela cualquier callback pendiente.

        No resetea el frame actual — usar `seek_frame(0)` para volver al
        inicio. Esto permite reanudar con `play()` desde donde se pausó.
        """
        self._playing = False
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def seek_frame(self, idx: int) -> None:
        """Salta a un frame específico y lo dibuja. No altera play/pause."""
        if self._img is None or self._n_frames == 0:
            return
        self._current_frame = max(0, min(int(idx), self._n_frames - 1))
        self._render_current_frame()

    def seek_ms(self, ms: int) -> None:
        """Salta al primer frame cuyo tiempo acumulado supere `ms`."""
        if self._img is None or self._n_frames == 0:
            return
        target = max(0, int(ms))
        acc = 0
        for i, d in enumerate(self._frame_durations):
            if acc + d > target:
                self.seek_frame(i)
                return
            acc += d
        self.seek_frame(self._n_frames - 1)

    @property
    def n_frames(self) -> int:
        return self._n_frames

    @property
    def current_frame(self) -> int:
        return self._current_frame

    @property
    def total_duration_ms(self) -> int:
        return sum(self._frame_durations)

    @property
    def current_time_ms(self) -> int:
        return sum(self._frame_durations[: self._current_frame])

    # ─── Render interno ─────────────────────────────────────────────────
    def _render_current_frame(self) -> None:
        """Dibuja el frame actual con escalado opcional al tamaño del widget."""
        if self._img is None:
            return
        try:
            self._img.seek(self._current_frame)
            frame = self._img.convert("RGB")

            if self._scaled:
                w = self._label.winfo_width()
                h = self._label.winfo_height()
                # winfo_width devuelve 1 antes del primer Configure;
                # en ese caso evitamos resize y usamos tamaño nativo.
                if w > 10 and h > 10:
                    src_w, src_h = frame.size
                    scale = min(w / src_w, h / src_h)
                    new_w = max(1, int(src_w * scale))
                    new_h = max(1, int(src_h * scale))
                    if (new_w, new_h) != (src_w, src_h):
                        frame = frame.resize(
                            (new_w, new_h), Image.LANCZOS,
                        )

            self._photo = ImageTk.PhotoImage(frame)
            self._label.configure(image=self._photo)
        except Exception:
            # Si algo falla a mitad del loop, paramos en silencio para no
            # spammear la consola en cada tick fallido.
            self.stop()
            return

        cb = self.on_frame_change
        if cb is not None:
            try:
                cb(
                    self._current_frame,
                    self.current_time_ms,
                    self.total_duration_ms,
                )
            except Exception:
                pass

    def _schedule_next(self) -> None:
        if not self._playing or self._img is None:
            return
        # Tomar duración del frame ACTUAL antes de avanzar
        delay = (
            self._frame_durations[self._current_frame]
            if self._frame_durations else 45
        )
        # Avanzar y renderizar el siguiente
        self._current_frame = (self._current_frame + 1) % self._n_frames
        self._after_id = self.after(max(10, delay), self._tick)

    def _tick(self) -> None:
        if not self._playing:
            return
        self._render_current_frame()
        self._schedule_next()

    # ─── Cleanup ────────────────────────────────────────────────────────
    def _on_destroy(self, _event) -> None:
        self.stop()
        self._photo = None
        if self._img is not None:
            try:
                self._img.close()
            except Exception:
                pass
            self._img = None
