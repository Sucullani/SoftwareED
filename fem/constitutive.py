"""
Matriz constitutiva D para elasticidad plana.
Tensión plana y Deformación plana.
"""

import numpy as np

from config.settings import ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN


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
        factor = E / (1.0 - nu**2)
        D = factor * np.array([
            [1.0,  nu,            0.0],
            [nu,   1.0,           0.0],
            [0.0,  0.0,  (1.0 - nu) / 2.0],
        ])
    elif analysis_type == ANALYSIS_PLANE_STRAIN:
        factor = E / ((1.0 + nu) * (1.0 - 2.0 * nu))
        D = factor * np.array([
            [1.0 - nu,   nu,                 0.0],
            [nu,         1.0 - nu,            0.0],
            [0.0,        0.0,    (1.0 - 2.0 * nu) / 2.0],
        ])
    else:
        raise ValueError(f"Tipo de análisis no reconocido: {analysis_type}")

    return D
