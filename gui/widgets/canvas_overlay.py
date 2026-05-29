"""
CanvasOverlay — panel flotante draggable sobre el MeshCanvas.

Implementa el "Modo B" de la propuesta UX: en lugar de abrir un Toplevel
con decoración de OS, los módulos educativos muestran su contenido en un
Toplevel BORDERLESS (`overrideredirect(True)`) posicionado libremente en
coordenadas de pantalla. El alumno mantiene el contexto del modelo y al
mismo tiempo puede arrastrar el panel A UN COSTADO del MeshCanvas para
liberar la malla y clickear los elementos cubiertos.

Diseño:
    - El overlay es un Toplevel borderless transient del main_window. Esto
      lo libera del bounding box del parent (a diferencia del approach
      anterior con `ttk.Frame` + `place()`, que Tk recortaba al MeshCanvas).
    - `transient(root)` mantiene el Z-order: sigue encima del main window,
      no aparece como ventana suelta en la taskbar, sigue al minimizar.
    - Header con título + botón cerrar; arrastrable haciendo click+drag en
      el header (estilo CAD: panel acoplable que el usuario reposiciona).
    - Body expuesto como `self.body` — los módulos lo pueblan con sus
      controles + visualización.
    - Cierra vía botón × o llamada externa a `close()`. Dispara on_close
      callback para que el módulo limpie sus highlights del canvas.

Uso típico:
    overlay = CanvasOverlay(mesh_canvas, title="② Matriz B",
                            initial_pos=(24, 24), on_close=cleanup_fn)
    ttk.Label(overlay.body, text="...").pack()
    overlay.show()

API pública preservada (`show`, `close`, `set_title`, `reposition`, `body`)
para no romper a los CanvasOverlayModule existentes.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import (
    PHASE_PRE_COLOR, PHASE_PROC_COLOR, PHASE_POST_COLOR,
    OVERLAY_BG, OVERLAY_BORDER, OVERLAY_TITLE_FG,
)


# Color de la barra de header según fase del módulo. Coherente con la
# identidad visual de fases que ya usa la GUI principal.
PHASE_BAR_COLORS = {
    "pre":  PHASE_PRE_COLOR,
    "proc": PHASE_PROC_COLOR,
    "post": PHASE_POST_COLOR,
    None:   PHASE_PROC_COLOR,
}

# Constantes OVERLAY_BG / OVERLAY_BORDER / OVERLAY_TITLE_FG migradas a
# config/settings.py para que cualquier widget hijo (LatexExpressionImage,
# LatexStatusLabel) pueda matchear el bg sin importar desde gui/.
OVERLAY_BAR_PADX = 10
OVERLAY_BAR_PADY = 6


class CanvasOverlay(tk.Toplevel):
    """Panel flotante borderless draggable, posicionado en coords de pantalla.

    El parent es el widget de referencia (típicamente la `MeshCanvas`) para
    el cálculo del `initial_pos` relativo. La ventana en sí es un Toplevel
    independiente: puede moverse fuera del MeshCanvas (sobre el spreadsheet,
    fuera de la app, monitor secundario).

    Args:
        parent: Widget Tk de referencia. Se usa para (a) resolver el toplevel
                raíz al que hacer `transient`, (b) calcular las coords de
                pantalla iniciales a partir de `initial_pos` relativo.
        title: Texto del header.
        initial_pos: (x_px, y_px) relativos a la esquina sup-izq del parent.
                     Se traducen a coords de pantalla al hacer `show()`.
        on_close: callable() ejecutado al cerrar (limpieza de highlights).
        phase: "pre" / "proc" / "post" — define color de la barra de header.
        closable: Si False, el botón × se omite (caller controla el ciclo).
        width / height: Tamaño fijo en px (None = auto).
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        title: str = "",
        initial_pos: Tuple[int, int] = (24, 24),
        on_close: Optional[Callable[[], None]] = None,
        phase: Optional[str] = None,
        closable: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        # El parent del Toplevel debe ser el root window (no el MeshCanvas
        # frame). Lo resolvemos vía winfo_toplevel(); guardamos el parent
        # original como referencia para el initial_pos relativo.
        root = parent.winfo_toplevel()
        super().__init__(root)
        self._parent = parent
        # **NO** guardamos `root` como `self._root` — ese nombre shadowearía
        # el método `tk.Misc._root()` que Tkinter llama internamente desde
        # `nametowidget()` cada vez que se resuelve un path Tcl absoluto
        # (todas las llamadas a `winfo_children()` lo dispararon, fallando
        # con `TypeError: 'Window' object is not callable`). Si en el
        # futuro hace falta el root, usar `self.winfo_toplevel()` o un
        # nombre distinto como `self._root_window`.
        self._on_close = on_close
        self._closable = closable
        self._rel_x, self._rel_y = initial_pos
        self._fixed_size = (width, height)
        self._destroyed = False

        # Workaround Windows: ocultamos hasta haber configurado todo, así
        # evitamos el parpadeo de un Toplevel borderless apareciendo en
        # (0,0) durante un frame antes de moverse a su posición final.
        self.withdraw()

        # Borderless: sin decoración de OS (nuestra barra de header cumple
        # esa función).
        self.overrideredirect(True)

        # `transient(root)` ES NECESARIO con `overrideredirect=True`:
        # sin él, Windows trata al Toplevel como un *popup* clásico y lo
        # OCULTA automáticamente en cuanto el parent (canvas / main
        # window) recibe foco — lo que el usuario percibe como "se
        # elimina al hover/click sobre el canvas". `transient` lo
        # convierte en *tool window*: persiste visible mientras la app
        # tenga focus, vuelve junto al main al minimizar.
        #
        # Trampa que NOS quemó antes: combinar transient + destroy()
        # crashea la app en Windows. La solución actual es **nunca
        # llamar destroy()** (ver `close()` abajo, que solo hace
        # `withdraw()`). Mientras se cumpla esa regla, transient es
        # seguro.
        try:
            self.transient(root)
        except tk.TclError:
            pass

        # **NO** registrar WM_DELETE_WINDOW: para overrideredirect=True el
        # WM no envía esos eventos, y registrar el protocolo abre la
        # puerta a propagar el close al root en algunas builds Tk/Windows.

        # Borde sutil que define el panel.
        self.configure(borderwidth=1, relief="solid", bg=OVERLAY_BORDER)

        # ── Header con barra de color de fase + título + cerrar ───────
        bar_color = PHASE_BAR_COLORS.get(phase, PHASE_BAR_COLORS[None])
        self._header = tk.Frame(self, bg=bar_color, height=28, cursor="fleur")
        self._header.pack(fill="x", side="top")
        self._header.pack_propagate(False)

        self._title_lbl = tk.Label(
            self._header, text=title, bg=bar_color, fg=OVERLAY_TITLE_FG,
            font=("Segoe UI Semibold", 10), padx=OVERLAY_BAR_PADX,
            pady=OVERLAY_BAR_PADY, anchor="w", cursor="fleur",
        )
        self._title_lbl.pack(side="left", fill="x", expand=True)

        if closable:
            # Botón cerrar nativo tk para integrarse con el bg de la barra
            close_btn = tk.Label(
                self._header, text="✕", bg=bar_color, fg=OVERLAY_TITLE_FG,
                font=("Segoe UI", 11, "bold"), padx=10, cursor="hand2",
            )
            close_btn.pack(side="right")
            # Usamos <ButtonRelease-1> en lugar de <ButtonPress-1>: el
            # release garantiza que Tk terminó de procesar el press antes
            # de iniciar el tear-down del Toplevel. Si bindeáramos al press
            # y destruyéramos durante el handler, en Windows el evento
            # subsiguiente (release) llegaría a un widget destruido y
            # Tk podría propagar el cierre al main window.
            close_btn.bind("<ButtonRelease-1>",
                            lambda _e: self._request_close())
            close_btn.bind("<Enter>",
                           lambda _e: close_btn.configure(bg="#c0392b"))
            close_btn.bind("<Leave>",
                           lambda _e: close_btn.configure(bg=bar_color))

        # ── Body donde el módulo poblará su contenido ────────────────
        self.body = tk.Frame(self, bg=OVERLAY_BG, padx=8, pady=8,
                              highlightthickness=0,
                              highlightbackground=OVERLAY_BORDER)
        self.body.pack(fill="both", expand=True)

        # ── Drag por header ──────────────────────────────────────────
        for w in (self._header, self._title_lbl):
            w.bind("<ButtonPress-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

    # ── API pública ────────────────────────────────────────────────
    def show(self) -> None:
        """Muestra el overlay en su posición inicial (coords de pantalla).

        Resolución de tamaño: para cada eje que `OVERLAY_WIDTH/HEIGHT` deja
        en None, usamos el `winfo_reqXXX()` natural del contenido (igual que
        hacía `place(width=W)` antes — alto auto-ajustado a lo packed).
        """
        try:
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
        except tk.TclError:
            px = py = 0
        sx = px + self._rel_x
        sy = py + self._rel_y

        # Forzamos un layout pass para que winfo_req* refleje el contenido
        # ya empaquetado por build_overlay().
        self.update_idletasks()
        w, h = self._fixed_size
        final_w = int(w) if w is not None else self.winfo_reqwidth()
        final_h = int(h) if h is not None else self.winfo_reqheight()
        self.geometry(f"{final_w}x{final_h}+{int(sx)}+{int(sy)}")
        # Tras el layout pass, build_overlay() ya pobló el body (incluso con
        # widgets matplotlib pesados). Bloqueamos el wheel sobre TODO el árbol
        # — ver _consume_wheel_recursive para la razón.
        self._consume_wheel_recursive()
        self.deiconify()
        self.lift()

    def refit(self) -> None:
        """Re-ajusta el tamaño del overlay a su contenido ACTUAL, preservando
        la posición en pantalla.

        La geometría se fija UNA vez en `show()`; si el `body` cambia de
        tamaño después (p.ej. al expandir un `Expander` de derivación), el
        Toplevel NO crece solo y el contenido nuevo queda recortado. Este
        método recalcula el tamaño (respetando los ejes con tamaño fijo
        `width`/`height` no-None; los None se toman de `winfo_req*`) y
        re-aplica la geometría sin mover la ventana (`geometry("WxH")` sin
        `+x+y` conserva la posición). Re-aplica también el bloqueo de rueda
        sobre los descendants nuevos (las imágenes LaTeX recién creadas)."""
        if self._destroyed:
            return
        try:
            self.update_idletasks()
            w, h = self._fixed_size
            final_w = int(w) if w is not None else self.winfo_reqwidth()
            final_h = int(h) if h is not None else self.winfo_reqheight()
            self.geometry(f"{final_w}x{final_h}")
            self._consume_wheel_recursive()
        except tk.TclError:
            pass

    def _consume_wheel_recursive(self) -> None:
        """Bind <MouseWheel> -> 'break' en este Toplevel y todos sus descendants.

        Motivación (regla 1A del diagnóstico de overlays educativos):
        cuando el alumno scrollea sobre el overlay flotante, NO queremos
        que el evento llegue a:
          (a) la MeshCanvas debajo (tiene focus por `<Enter>` y haría
              zoom no intencional);
          (b) el FigureCanvasTkAgg de matplotlib embebido — en algunas
              builds Tk/Windows su handler interno reconfigura el widget,
              y esa operación dentro de un widget hijo de un Toplevel
              `overrideredirect=True + transient(root)` dispara WM_CLOSE
              al root y cierra la app entera (regla de oro #3 documentada
              en este archivo).

        Recorremos los descendants porque `bind` sobre el Toplevel sólo
        atrapa eventos delivered directamente a él; los hijos lo evitan
        salvo que se manipulen bindtags. Es más simple bindear cada
        descendant: los binds instance-level corren ANTES que los
        class-level y `return "break"` corta la propagación por bindtags.
        """
        def _walk(w):
            # Captura amplia: además de TclError (widget destruido / no Tk),
            # algunos widgets de terceros (matplotlib, ttkbootstrap, etc.)
            # exponen atributos que pueden confundir a Tkinter al inspeccionar
            # su árbol — no queremos que un widget exótico aborte el walk.
            try:
                w.bind("<MouseWheel>", lambda _e: "break")
            except Exception:
                pass
            try:
                children = w.winfo_children()
            except Exception:
                return
            for child in children:
                _walk(child)
        _walk(self)

    def set_title(self, text: str) -> None:
        """Actualiza el texto del header sin reconstruir el overlay."""
        try:
            self._title_lbl.configure(text=text)
        except tk.TclError:
            pass

    def _request_close(self) -> None:
        """Punto de entrada del botón × del header.

        Se invoca desde `<ButtonRelease-1>` del close button. NO ejecuta
        el cierre directamente: lo difiere via `after_idle` para que Tk
        termine completamente de procesar el evento del release antes de
        que toquemos el widget tree. En Windows, ejecutar withdraw/destroy
        dentro del handler del press/release de un widget hijo de un
        Toplevel con `overrideredirect=True` causa que el WM propague un
        WM_CLOSE al root y mate la app entera.
        """
        if self._destroyed:
            return
        try:
            self.after_idle(self.close)
        except tk.TclError:
            self.close()

    def close(self) -> None:
        """Cierra el overlay y dispara el callback on_close (una sola vez).

        IMPORTANTE — **nunca llamar a `destroy()` sobre este Toplevel**:
        en Windows, destruir un Toplevel `overrideredirect=True` puede
        propagar un WM_CLOSE al root window y matar la app entera. En su
        lugar, hacemos `withdraw()` (oculta la ventana y libera grab/focus
        sin destruir el handle WM). El Toplevel queda como objeto Python
        retenido por el GC del módulo educativo; cuando el módulo se
        recicla, el Toplevel también es elegible para GC (Tcl/Tk lo
        recoge en el siguiente ciclo del intérprete).

        Trade-off: un Toplevel "fantasma" por módulo educativo abierto y
        cerrado. Es bounded (singleton por clase), unas decenas de KB.
        Aceptable frente al crash.
        """
        if self._destroyed:
            return
        self._destroyed = True
        cb = self._on_close
        # Ocultar SIN destruir — visualmente el panel se va al instante.
        try:
            self.withdraw()
        except tk.TclError:
            pass
        # Limpieza del módulo: callbacks del canvas se restauran ahora.
        if cb is not None:
            try:
                cb()
            except Exception:
                pass

    def reposition(self, x_screen: int, y_screen: int) -> None:
        """Mueve el overlay a coordenadas (x, y) de PANTALLA.

        A diferencia de la versión basada en `place()`, ya no se clampea
        contra el bounding box del parent — el usuario puede arrastrar el
        panel a cualquier parte del escritorio (sobre el spreadsheet, o
        a un monitor secundario). Solo aplicamos un clamp suave contra
        los bordes de pantalla del monitor primario para que el header
        siempre siga siendo agarrable (no se "pierde" fuera del escritorio).
        """
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w = max(1, self.winfo_width())
            h = max(1, self.winfo_height())
        except tk.TclError:
            sw = sh = 10_000
            w = h = 1
        # Permitimos que la mayor parte salga del screen, pero exigimos al
        # menos 80×24 px de header visible para que se pueda re-agarrar.
        margin_x = max(80, min(w, 200))
        margin_y = 24
        x = max(-(w - margin_x), min(int(x_screen), sw - margin_x))
        y = max(0, min(int(y_screen), sh - margin_y))
        try:
            self.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    # ── Drag interno ──────────────────────────────────────────────
    def _start_drag(self, event: tk.Event) -> None:
        # Guardamos offset del cursor dentro de la ventana en el momento
        # del press. event.x / event.y son coords del widget que recibió
        # el binding (header), que está pegado al borde superior del
        # Toplevel → coinciden con offset dentro del Toplevel.
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _on_drag(self, event: tk.Event) -> None:
        # Coords de pantalla absolutas — restamos el offset del press para
        # que el cursor se mantenga sobre el mismo punto del header.
        nx = event.x_root - self._drag_dx
        ny = event.y_root - self._drag_dy
        self.reposition(nx, ny)
