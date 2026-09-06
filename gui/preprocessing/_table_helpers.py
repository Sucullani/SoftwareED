"""
Utilidades compartidas para los Treeview del panel de preproceso.

Sin estado: cada funcion crea widgets/bindings y devuelve el widget creado
(o None) para que el llamador maneje su ciclo de vida.

Funciones:
- start_cell_editor: Entry flotante de alto contraste sobre una celda.
    Su `on_commit` ahora recibe (text, direction) donde direction in
    {"none", "return", "tab", "shift-tab", "down", "up"} para soportar
    navegacion estilo Excel (Tab/Shift-Tab/Enter/flechas).
- start_combobox_editor: Combobox readonly en un Toplevel overlay para que
    el dropdown pueda desbordar el Treeview sin clipping.
- bind_clipboard: copy/paste TSV (Ctrl+C / Ctrl+V) compatible con Excel.
- to_float_flex: float() que tolera la coma decimal de Excel en español.
"""

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import (
    FONT_UI_LARGE,
    CANVAS_SELECTED_ROW_FG,
    LABEL_FG,
    EDITOR_ENTRY_BG,
    EDITOR_ENTRY_FG,
    EDITOR_FOCUS_BORDER_COLOR,
    POPUP_BG,
    POPUP_LIST_BG,
    POPUP_SELECT_BG,
)


# ─── Conversion numerica tolerante ──────────────────────────────────────────


def to_float_flex(value) -> float:
    """`float()` que acepta la coma decimal de Excel en español.

    El separador decimal del proyecto es el punto, pero un Excel en español
    copia `1,5` al portapapeles. Sin este fallback los `_paste_*` descartaban
    esas filas en silencio. Eleva `ValueError` igual que `float()` cuando el
    texto no es un número, para que el `except` del llamador siga saltando
    la fila.
    """
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        return float(text.replace(",", "."))


# ─── Editores flotantes ─────────────────────────────────────────────────────

def start_cell_editor(tree, item, column, current_value,
                      on_commit, on_cancel=None, font=None):
    """Crea un Entry flotante sobre la celda (item, column) del Treeview.

    on_commit(text): callback con el texto ingresado al confirmar.
    on_cancel(): callback opcional al cancelar (Escape).
    font: tupla (familia, tamano). Default FONT_UI_LARGE para que coincida
        con la fuente del Treeview y el texto no "salte" al editar.

    Bindings: Return / KP_Enter / FocusOut commit, Escape cancela.
    No hay navegacion entre celdas via Tab/flechas — esa funcionalidad
    fue removida intencionalmente.

    Retorna el Entry, o None si la celda no es visible.
    """
    tree.see(item)
    tree.update_idletasks()
    bbox = tree.bbox(item, column)
    if not bbox:
        return None

    entry = tk.Entry(
        tree,
        font=font or FONT_UI_LARGE,
        bg=EDITOR_ENTRY_BG,
        fg=EDITOR_ENTRY_FG,
        relief="solid",
        bd=1,
        highlightthickness=2,
        highlightbackground=EDITOR_FOCUS_BORDER_COLOR,
        highlightcolor=EDITOR_FOCUS_BORDER_COLOR,
        insertbackground=EDITOR_ENTRY_FG,
        justify="center",
    )
    entry.place(x=bbox[0] - 1, y=bbox[1] - 1,
                width=bbox[2] + 2, height=bbox[3] + 2)
    entry.insert(0, "" if current_value is None else str(current_value))
    entry.select_range(0, tk.END)
    entry.icursor(tk.END)
    entry.focus_force()

    state = {"done": False}

    def _commit(_e=None):
        if state["done"]:
            return
        state["done"] = True
        text = entry.get()
        try:
            entry.destroy()
        except tk.TclError:
            pass
        on_commit(text)

    def _cancel(_e=None):
        if state["done"]:
            return
        state["done"] = True
        try:
            entry.destroy()
        except tk.TclError:
            pass
        if on_cancel:
            on_cancel()

    entry.bind("<Return>",   _commit)
    entry.bind("<KP_Enter>", _commit)
    entry.bind("<FocusOut>", _commit)
    entry.bind("<Escape>",   _cancel)
    return entry


def start_combobox_editor(tree, item, column, current_value, options,
                          on_commit, on_cancel=None, font=None):
    """Dropdown custom: Toplevel + Listbox bajo la celda clickeada.

    En lugar de `ttk.Combobox` (cuyo popup es manejado internamente por Tk
    y que en algunas combinaciones tema/plataforma se renderiza incompleto
    o queda recortado), usamos un Toplevel `overrideredirect=True` con un
    Listbox dentro, posicionado en coordenadas absolutas de pantalla. El
    usuario ve la lista completa de materiales sin clipping.

    Comportamiento:
    - Click en una opcion -> commit.
    - Up/Down -> navegacion; Enter -> commit; Escape -> cancel.
    - FocusOut o click fuera -> cancel.

    Mismo contrato: `on_commit(value)` recibe el string seleccionado.
    """
    import tkinter.font as tkfont

    tree.see(item)
    tree.update_idletasks()
    bbox = tree.bbox(item, column)
    if not bbox:
        return None

    cell_font = font or FONT_UI_LARGE
    options = list(options)
    if not options:
        return None

    # Coordenadas absolutas en pantalla
    x_root = tree.winfo_rootx() + bbox[0]
    y_root = tree.winfo_rooty() + bbox[1] + bbox[3]  # justo debajo de la celda

    # Dimensionar la ventana
    f = tkfont.Font(family=cell_font[0], size=cell_font[1])
    char_px = f.measure("M")
    max_text_px = max((f.measure(str(o)) for o in options), default=100)
    width_px = max(bbox[2], max_text_px + 24)
    row_px = f.metrics("linespace") + 6
    n_visible = min(max(len(options), 3), 12)
    height_px = row_px * n_visible + 4

    popup = tk.Toplevel(tree)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.geometry(f"{int(width_px)}x{int(height_px)}+{int(x_root)}+{int(y_root)}")
    popup.configure(bg=POPUP_BG)

    listbox = tk.Listbox(
        popup,
        font=cell_font,
        bg=POPUP_LIST_BG,
        fg=LABEL_FG,
        selectbackground=POPUP_SELECT_BG,
        selectforeground=CANVAS_SELECTED_ROW_FG,
        activestyle="none",
        relief="flat",
        bd=0,
        highlightthickness=0,
        exportselection=False,
    )
    listbox.pack(fill="both", expand=True, padx=1, pady=1)
    for opt in options:
        listbox.insert("end", str(opt))

    # Resaltar valor actual
    try:
        idx = options.index(current_value)
    except (ValueError, TypeError):
        idx = 0
    listbox.selection_set(idx)
    listbox.activate(idx)
    listbox.see(idx)
    listbox.focus_force()

    state = {"done": False}

    def _destroy_popup():
        try:
            popup.destroy()
        except tk.TclError:
            pass

    def _commit(_e=None):
        if state["done"]:
            return
        sel = listbox.curselection()
        if not sel:
            value = current_value
        else:
            value = options[sel[0]]
        state["done"] = True
        _destroy_popup()
        on_commit(value)
        return "break"

    def _cancel(_e=None):
        if state["done"]:
            return
        state["done"] = True
        _destroy_popup()
        if on_cancel:
            on_cancel()
        return "break"

    listbox.bind("<<ListboxSelect>>", lambda e: None)
    listbox.bind("<Double-1>", _commit)
    listbox.bind("<Return>", _commit)
    listbox.bind("<KP_Enter>", _commit)
    listbox.bind("<Escape>", _cancel)
    listbox.bind("<FocusOut>", _cancel)
    # Single-click selecciona y confirma (UX rapida tipo combobox)
    listbox.bind("<ButtonRelease-1>",
                 lambda e: popup.after(10, _commit))

    return listbox


# ─── Clipboard TSV (copy/paste con Excel) ───────────────────────────────────

def bind_clipboard(tree, copy_serializer, paste_handler):
    """Bindea Ctrl+C y Ctrl+V al Treeview para copy/paste TSV con Excel.

    copy_serializer(iid) -> list[str] | None
        Para cada fila seleccionada devuelve los valores como strings.
        Devuelve None para excluir la fila (p.ej. placeholder).

    paste_handler(rows: list[list[str]]) -> None
        Recibe la matriz parseada del clipboard. El handler valida y
        aplica los cambios al modelo (incluyendo refresh y redraw final).
    """

    def _copy(_e=None):
        sel = tree.selection()
        if not sel:
            return "break"
        lines = []
        for iid in sel:
            row = copy_serializer(iid)
            if row is None:
                continue
            lines.append("\t".join("" if v is None else str(v) for v in row))
        if not lines:
            return "break"
        try:
            tree.clipboard_clear()
            tree.clipboard_append("\n".join(lines))
        except tk.TclError:
            pass
        return "break"

    def _paste(_e=None):
        try:
            text = tree.clipboard_get()
        except tk.TclError:
            return "break"
        if not text:
            return "break"
        rows = []
        for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            if not raw.strip():
                continue
            rows.append(raw.split("\t"))
        if not rows:
            return "break"
        paste_handler(rows)
        return "break"

    tree.bind("<Control-c>", _copy)
    tree.bind("<Control-C>", _copy)
    tree.bind("<Control-v>", _paste)
    tree.bind("<Control-V>", _paste)
