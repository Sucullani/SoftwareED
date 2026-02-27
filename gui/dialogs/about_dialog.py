"""
AboutDialog: Ventana "Acerca de..." del software.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import APP_NAME, APP_VERSION, APP_AUTHOR


class AboutDialog:
    """Ventana de información Acerca de EduFEM."""

    def __init__(self, parent):
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Acerca de EduFEM")
        self.dialog.geometry("450x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        main = ttk.Frame(self.dialog, padding=25)
        main.pack(fill=BOTH, expand=YES)

        # Logo / Título
        ttk.Label(
            main,
            text="📐 EduFEM",
            font=("Segoe UI", 22, "bold"),
            bootstyle="primary",
        ).pack(pady=(0, 5))

        ttk.Label(
            main,
            text="Software Educativo de Elementos Finitos",
            font=("Segoe UI", 11),
            foreground="#aaa",
        ).pack()

        ttk.Separator(main).pack(fill=X, pady=15)

        # Info
        info_text = (
            f"Versión: {APP_VERSION}\n\n"
            f"Desarrollado como parte de:\n"
            f"{APP_AUTHOR}\n\n"
            f"Método de Elementos Finitos\n"
            f"Elementos Isoparamétricos Q4 y Q9\n"
            f"Tensión Plana y Deformación Plana\n\n"
            f"Python + tkinter + NumPy + Matplotlib"
        )

        ttk.Label(
            main,
            text=info_text,
            font=("Segoe UI", 10),
            justify=CENTER,
            foreground="#ccc",
        ).pack()

        ttk.Separator(main).pack(fill=X, pady=15)

        ttk.Button(
            main, text="Cerrar", bootstyle="secondary",
            command=self.dialog.destroy, width=12
        ).pack()

        # Centrar
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 350) // 2
        self.dialog.geometry(f"+{x}+{y}")
