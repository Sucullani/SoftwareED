"""
Matriz constitutiva D para elasticidad plana.
Tensión plana y Deformación plana.

Implementacion JIT: el kernel `_constitutive_matrix_njit` recibe un flag
entero (0=plane stress, 1=plane strain) porque Numba no soporta bien
comparaciones de strings. El wrapper `constitutive_matrix` hace el
dispatch desde el string del project a ese flag.
"""

import numpy as np

from config.settings import ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN
from fem._numba_compat import njit


# Flags internos para el kernel JIT.
_FLAG_PLANE_STRESS = 0
_FLAG_PLANE_STRAIN = 1


@njit(cache=True)
def _constitutive_matrix_njit(E, nu, flag):
    """Kernel JIT: arma D (3x3) con flag entero.

    flag = 0 -> Tension Plana (sigma_z = 0).
    flag = 1 -> Deformacion Plana (epsilon_z = 0).
    """
    D = np.zeros((3, 3))
    if flag == 0:
        factor = E / (1.0 - nu * nu)
        D[0, 0] = factor * 1.0
        D[0, 1] = factor * nu
        D[1, 0] = factor * nu
        D[1, 1] = factor * 1.0
        D[2, 2] = factor * (1.0 - nu) / 2.0
    else:  # flag == 1, plane strain
        factor = E / ((1.0 + nu) * (1.0 - 2.0 * nu))
        D[0, 0] = factor * (1.0 - nu)
        D[0, 1] = factor * nu
        D[1, 0] = factor * nu
        D[1, 1] = factor * (1.0 - nu)
        D[2, 2] = factor * (1.0 - 2.0 * nu) / 2.0
    return D


def constitutive_matrix(E, nu, analysis_type):
    """
    Calcula la matriz constitutiva D (3×3).

    Tensión Plana (σz = 0):
        D = E/(1-ν²) * [[1,  ν,      0        ],
                         [ν,  1,      0        ],
                         [0,  0,  (1-ν)/2      ]]

    Deformación Plana (εz = 0):
        D = E/((1+ν)(1-2ν)) * [[1-ν,  ν,       0        ],
                                [ν,    1-ν,     0        ],
                                [0,    0,    (1-2ν)/2    ]]

    Retorna: D array (3, 3)
    """
    if analysis_type == ANALYSIS_PLANE_STRESS:
        return _constitutive_matrix_njit(E, nu, _FLAG_PLANE_STRESS)
    elif analysis_type == ANALYSIS_PLANE_STRAIN:
        return _constitutive_matrix_njit(E, nu, _FLAG_PLANE_STRAIN)
    else:
        raise ValueError(f"Tipo de análisis no reconocido: {analysis_type}")
