"""
fem.symbolic_integrand — construcción SIMBÓLICA (SymPy) del integrando de la
matriz de rigidez elemental Q4:  [Bᵀ D B |det J| t](ξ, η).

Es código puro SymPy/NumPy (sin Tk/matplotlib), motivado pedagógicamente: el
integrando de k_e crece a una expresión racional gigante en (ξ, η), lo que
justifica por qué se integra numéricamente con cuadratura de Gauss en vez de
analíticamente.

Consumidores:
  - education.mod05_stiffness  (overlay M5, expander "¿por qué no se puede
    integrar a mano?")
  - file_io.memoria_calculo    (PDF de memoria, paso a paso del integrando)

Vivía en education/mod05_stiffness.py; se movió aquí en 2026-05 para romper el
acoplamiento file_io → education (la memoria PDF lo importaba arrastrando todo
el stack Tk/matplotlib de un módulo overlay). La capa file_io → fem es correcta.
"""

from __future__ import annotations

import sympy as sp

from config.settings import ANALYSIS_PLANE_STRESS, MATRIX_DISPLAY_ZERO_REL_TOL


def podar_ruido(expr, tol: float = MATRIX_DISPLAY_ZERO_REL_TOL):
    r"""Borra de cada suma los términos cuyo coeficiente numérico es
    despreciable frente al mayor de ESA misma suma.

    Las coordenadas de los nodos entran como flotantes, así que al armar el
    Jacobiano de un elemento RECTANGULAR —donde la teoría dice que los
    términos cruzados son exactamente cero— sympy arrastra el redondeo y
    escribe cosas como::

        (1.06581410364015e-13*eta - 750.0)**2

    Eso no es solo feo: impide que sympy pliegue el paréntesis a ``562500.0``,
    de modo que la expresión de $K_{11}$ queda con cientos de términos que la
    teoría no tiene. En la Memoria se emite dentro de un ``equation*``, que no
    admite corte de línea, y el resultado medido eran **566 pt de fórmula
    impresa fuera de la hoja** (Timoshenko Q4), invisibles para el alumno.

    El criterio es RELATIVO, igual que el de las matrices que se muestran en
    pantalla (`config.settings.MATRIX_DISPLAY_ZERO_REL_TOL`): un coeficiente
    doce órdenes menor que su vecino en la misma suma es ruido de doble
    precisión, no un dato. Los términos simbólicos sin coeficiente numérico
    legible se conservan siempre.

    Función pura: no toca el cálculo, solo la expresión que se va a mostrar.
    """
    def _recorre(e):
        if e.is_Add:
            terminos = [_recorre(t) for t in e.args]
            magnitudes = []
            for t in terminos:
                coef, _ = t.as_coeff_Mul()
                try:
                    magnitudes.append(abs(float(coef)))
                except (TypeError, ValueError):
                    magnitudes.append(float("inf"))   # sin número: se queda
            finitas = [m for m in magnitudes if m != float("inf")]
            mayor = max(finitas) if finitas else 0.0
            if mayor > 0.0:
                piso = mayor * tol
                terminos = [t for t, m in zip(terminos, magnitudes)
                            if m > piso]
            return sp.Add(*terminos) if terminos else sp.Integer(0)
        if e.args:
            return e.func(*[_recorre(a) for a in e.args])
        return e

    return sp.simplify(_recorre(sp.sympify(expr)))


class SymbolicIntegrandQ4:
    """Construcción simbólica de [B^T D B |det J| t] para Q4."""

    def __init__(self, E=225000.0, nu=0.2, t=0.8, coords=None):
        self.E = E
        self.nu = nu
        self.t = t
        self.coords = coords if coords is not None else [
            [0, 0], [5, 0], [7, 4], [2, 3]
        ]
        self.xi, self.eta = sp.symbols(r"\xi \eta", real=True)

    def _shape_functions(self):
        xi, eta = self.xi, self.eta
        return [
            sp.Rational(1, 4) * (1 - xi) * (1 - eta),
            sp.Rational(1, 4) * (1 + xi) * (1 - eta),
            sp.Rational(1, 4) * (1 + xi) * (1 + eta),
            sp.Rational(1, 4) * (1 - xi) * (1 + eta),
        ]

    def _jacobian(self, dN_dxi, dN_deta):
        c = self.coords
        dx_dxi  = sum(dN_dxi[i]  * c[i][0] for i in range(4))
        dy_dxi  = sum(dN_dxi[i]  * c[i][1] for i in range(4))
        dx_deta = sum(dN_deta[i] * c[i][0] for i in range(4))
        dy_deta = sum(dN_deta[i] * c[i][1] for i in range(4))
        return sp.Matrix([[dx_dxi, dy_dxi], [dx_deta, dy_deta]])

    def _b(self, dN_dxi, dN_deta, J):
        detJ = J.det()
        i11 =  J[1, 1] / detJ
        i12 = -J[0, 1] / detJ
        i21 = -J[1, 0] / detJ
        i22 =  J[0, 0] / detJ
        B_parts = []
        for i in range(4):
            dNx = i11 * dN_dxi[i] + i12 * dN_deta[i]
            dNy = i21 * dN_dxi[i] + i22 * dN_deta[i]
            B_parts.append(sp.Matrix([[dNx, 0], [0, dNy], [dNy, dNx]]))
        return sp.Matrix.hstack(*B_parts), detJ

    def _d(self, analysis):
        E = sp.Rational(self.E).limit_denominator(1_000_000)
        nu = sp.Rational(self.nu).limit_denominator(1000)
        if analysis == ANALYSIS_PLANE_STRESS:
            f = E / (1 - nu ** 2)
            return f * sp.Matrix([
                [1,  nu, 0],
                [nu, 1,  0],
                [0,  0,  (1 - nu) / 2],
            ])
        f = E / ((1 + nu) * (1 - 2 * nu))
        return f * sp.Matrix([
            [1 - nu, nu,    0],
            [nu,     1 - nu, 0],
            [0,      0,      (1 - 2 * nu) / 2],
        ])

    def integrand_entry(self, i, j, analysis):
        Ns = self._shape_functions()
        dN_dxi  = [sp.diff(N, self.xi)  for N in Ns]
        dN_deta = [sp.diff(N, self.eta) for N in Ns]
        J = self._jacobian(dN_dxi, dN_deta)
        B, detJ = self._b(dN_dxi, dN_deta, J)
        D = self._d(analysis)
        K = (B.T * D * B) * sp.Abs(detJ) * sp.Rational(self.t).limit_denominator(1000)
        return sp.simplify(K[i, j])
