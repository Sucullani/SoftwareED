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
- make_context_menu: menu contextual click-derecho con items dinamicos.
- bind_clipboard: copy/paste TSV (Ctrl+C / Ctrl+V) compatible con Excel.
- bind_fill_down: Ctrl+D para propagar el valor de la celda activa de la
    primera fila seleccionada hacia abajo en el resto de la seleccion.
"""

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import FONT_UI_LARGE


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
        bg="#ffffff",
        fg="#000000",
        relief="solid",
        bd=1,
        highlightthickness=2,
        highlightbackground="#3399ff",
        highlightcolor="#3399ff",
        insertbackground="#000000",
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
    popup.configure(bg="#3a3d42")

    listbox = tk.Listbox(
        popup,
        font=cell_font,
        bg="#1c1e22",
        fg="#e8e8ea",
        selectbackground="#1f6feb",
        selectforeground="#ffffff",
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


# ─── Menu contextual ────────────────────────────────────────────────────────

def make_context_menu(tree, items):
    """Crea un menu contextual y lo bindea a click-derecho del Treeview.

    items: lista de tuplas. Soporta varios formatos:
      - (label, callback)                         → siempre habilitado
      - (label, callback, enabled_predicate)      → habilitado segun predicado
      - ("---", None)                             → separator
    El predicate recibe el iid de la fila clickeada y devuelve bool.
    Devuelve el Menu (para reconfigurar items si hace falta).
    """
    menu = tk.Menu(tree, tearoff=0)

    def _popup(event):
        row = tree.identify_row(event.y)
        if row and row not in tree.selection():
            tree.selection_set(row)
        menu.delete(0, "end")
        for entry in items:
            if len(entry) == 2 and entry[0] == "---":
                menu.add_separator()
                continue
            label = entry[0]
            cb = entry[1]
            pred = entry[2] if len(entry) >= 3 else None
            state = "normal"
            if pred is not None:
                try:
                    state = "normal" if pred(row) else "disabled"
                except Exception:
                    state = "disabled"
            menu.add_command(label=label, command=cb, state=state)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    tree.bind("<Button-3>", _popup)
    return menu


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


# ─── Fill-down (Ctrl+D estilo Excel) ────────────────────────────────────────

def bind_fill_down(tree, get_cell_value, set_cell_value, refresh,
                   skip_iids=None):
    """Bindea Ctrl+D para propagar el valor de una columna hacia abajo.

    Toma como fuente la PRIMERA fila seleccionada y la columna sobre la que
    esta el puntero (o la #1 si no se puede inferir). Aplica ese valor a las
    demas filas seleccionadas (excluyendo las que esten en skip_iids).

    get_cell_value(iid, column_id) -> str
    set_cell_value(iid, column_id, value) -> None  (debe mutar el modelo)
    refresh() -> None  (un solo refresh + redraw al final)
    skip_iids: iterable de iids a excluir (p.ej. {"__new__"}).
    """
    skip = set(skip_iids or ())

    def _fill(_e=None):
        sel = tree.selection()
        sel = [iid for iid in sel if iid not in skip]
        if len(sel) < 2:
            return "break"
        # Inferir columna activa segun donde este el cursor
        try:
            col = tree.identify_column(
                tree.winfo_pointerx() - tree.winfo_rootx())
        except tk.TclError:
            col = "#1"
        if not col:
            col = "#1"
        source_iid = sel[0]
        try:
            value = get_cell_value(source_iid, col)
        except Exception:
            return "break"
        for iid in sel[1:]:
            try:
                set_cell_value(iid, col, value)
            except Exception:
                continue
        refresh()
        return "break"

    tree.bind("<Control-d>", _fill)
    tree.bind("<Control-D>", _fill)
