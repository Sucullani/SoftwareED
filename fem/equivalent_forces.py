"""
Conversion de cargas distribuidas a fuerzas nodales equivalentes.

Carga superficial trapezoidal sobre una arista de 2 nodos:
    q(s) = q_start * (1-s)/2 + q_end * (1+s)/2,    s en [-1, 1]
Con funciones de forma lineales N_1(s)=(1-s)/2, N_2(s)=(1+s)/2 y
jacobiano de la arista = L/2:
    F_i = ∫_{-1}^{1} N_i(s) · q(s) · (L/2) · ds
Integracion exacta (la integral es polinomial de grado 2):
    F_1 = (L/6) * (2*q_start + q_end)
    F_2 = (L/6) * (q_start + 2*q_end)

Estas fuerzas se aplican en la direccion del vector de carga, definido por:
    n0 = normal EXTERIOR a la arista (rotacion -90° del tangente, o sea
         (ty, -tx) — apunta hacia afuera del elemento si la conectividad
         es CCW, que es la convencion del proyecto).  angle=0 ⇒ carga
         empujando en la direccion de la normal exterior (tipica presion
         superficial comprimiendo el elemento).
    direccion = R(angle) · n0   (rotacion adicional CCW, angle en grados).
"""

import math


def surface_load_to_nodal_forces(p_start, p_end,
                                 q_start, q_end, angle_deg=0.0):
    """Fuerzas nodales equivalentes para una carga superficial trapezoidal.

    Args:
        p_start: (x1, y1) coordenadas en mundo del nodo inicial.
        p_end:   (x2, y2) coordenadas en mundo del nodo final.
        q_start: magnitud de q en p_start (fuerza por unidad de longitud).
        q_end:   magnitud de q en p_end.
        angle_deg: angulo en grados respecto a la normal exterior (CCW).

    Returns:
        ((fx_start, fy_start), (fx_end, fy_end))  en coordenadas globales.
    """
    x1, y1 = p_start
    x2, y2 = p_end
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L < 1e-15:
        return (0.0, 0.0), (0.0, 0.0)

    # Tangente unitaria y normal EXTERIOR (rotacion -90° del tangente) para
    # elementos con conectividad CCW — convencion del proyecto.
    tx, ty = dx / L, dy / L
    nx0, ny0 = ty, -tx

    # Rotacion adicional por angle_deg (CCW)
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    dx_dir = c * nx0 - s * ny0
    dy_dir = s * nx0 + c * ny0

    # Magnitudes integradas (formula exacta para carga lineal en 2-nodos)
    F_start_mag = L / 6.0 * (2.0 * q_start + q_end)
    F_end_mag = L / 6.0 * (q_start + 2.0 * q_end)

    return (
        (F_start_mag * dx_dir, F_start_mag * dy_dir),
        (F_end_mag * dx_dir,   F_end_mag * dy_dir),
    )


def surface_load_to_nodal_forces_q9(p_start, p_mid, p_end,
                                    q_start, q_end, angle_deg=0.0):
    """Fuerzas nodales equivalentes para una arista Q9 de 3 nodos.

    Funciones de forma 1D cuadráticas:
        N1(s) = s(s-1)/2,  N2(s) = 1 - s²,  N3(s) = s(s+1)/2,  s in [-1, 1]
    Carga q lineal entre q_start (s=-1) y q_end (s=+1):
        q(s) = q_start * (1-s)/2 + q_end * (1+s)/2
    Integración con 2 puntos Gauss 1D (integrando de grado 3, exacto).
    Se asume arista recta con nodo medio colocado en el centro; el jacobiano
    de la arista se reduce a L/2 y la dirección de carga es constante.

    Args:
        p_start, p_mid, p_end: coordenadas (x, y) de los 3 nodos de la arista.
        q_start, q_end:        magnitudes de q en los extremos.
        angle_deg:             ángulo respecto a la normal exterior (CCW).

    Returns:
        ((fx_s, fy_s), (fx_m, fy_m), (fx_e, fy_e)) en coords globales.
    """
    x1, y1 = p_start
    x3, y3 = p_end
    dx, dy = x3 - x1, y3 - y1
    L = math.hypot(dx, dy)
    if L < 1e-15:
        return (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)

    # Normal EXTERIOR (rotacion -90° del tangente) — ver docstring del modulo.
    tx, ty = dx / L, dy / L
    nx0, ny0 = ty, -tx

    th = math.radians(angle_deg)
    c, s_th = math.cos(th), math.sin(th)
    dx_dir = c * nx0 - s_th * ny0
    dy_dir = s_th * nx0 + c * ny0

    # Gauss 2 puntos en [-1, 1]
    gp = 1.0 / math.sqrt(3.0)
    gauss_pts = (-gp, gp)
    weights = (1.0, 1.0)

    F_mag = [0.0, 0.0, 0.0]  # start, mid, end
    for s, w in zip(gauss_pts, weights):
        N1 = s * (s - 1.0) / 2.0
        N2 = 1.0 - s * s
        N3 = s * (s + 1.0) / 2.0
        q_s = q_start * (1.0 - s) / 2.0 + q_end * (1.0 + s) / 2.0
        J = L / 2.0
        F_mag[0] += N1 * q_s * J * w
        F_mag[1] += N2 * q_s * J * w
        F_mag[2] += N3 * q_s * J * w

    return (
        (F_mag[0] * dx_dir, F_mag[0] * dy_dir),
        (F_mag[1] * dx_dir, F_mag[1] * dy_dir),
        (F_mag[2] * dx_dir, F_mag[2] * dy_dir),
    )
