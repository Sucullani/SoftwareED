"""Wrapper para Numba con fallback a Python puro.

Permite decorar funciones con `@njit` en `fem/` y `gui/` sin obligar a
que Numba este instalado. Si Numba esta disponible (caso normal), los
decoradores compilan a maquina via LLVM y dan 5-30x speedup en los hot
paths numericos. Si no esta, `njit` se convierte en no-op y el codigo
corre en Python puro — mas lento pero funcional.

Uso canonico (al inicio de un modulo numerico):

    from fem._numba_compat import njit, prange

    @njit(cache=True)
    def hot_function(x):
        ...

Notas:
- `cache=True` persiste la compilacion en `__pycache__` — la primera
  ejecucion compila (~1-3 s warmup), las siguientes leen del disco.
- `fastmath=True` permite reordenamientos numericos que pueden cambiar
  el ultimo bit. Usarlo solo en rasterizado / visualizacion, NO en el
  pipeline FEM (V&V exige bit-reproducibilidad).
- `parallel=True` + `prange` paralelizan loops sobre elementos. Aplica
  solo cuando no hay race conditions (rasterizado por elemento sobre
  un buffer compartido SI tiene race; ensamblaje COO con `coo_data`
  acumulado por elemento NO si cada elemento escribe a su propio slot).
"""

try:
    from numba import njit as _njit, prange as _prange
    HAS_NUMBA = True

    def njit(*args, **kwargs):
        """Reexporta `numba.njit` para que `from fem._numba_compat import
        njit` funcione identico a `from numba import njit`."""
        return _njit(*args, **kwargs)

    def prange(*args, **kwargs):
        """Reexporta `numba.prange` para uso en loops paralelos."""
        return _prange(*args, **kwargs)

except ImportError:
    HAS_NUMBA = False

    def njit(*args, **kwargs):
        """Fallback no-op cuando Numba no esta disponible.

        Acepta los dos patrones de uso:
        - `@njit` (sin parentesis): args[0] es la funcion.
        - `@njit(cache=True, ...)` (con kwargs): retorna un decorator.
        """
        if len(args) == 1 and callable(args[0]) and not kwargs:
            # @njit sin parentesis: args[0] es la funcion.
            return args[0]

        def decorator(fn):
            return fn
        return decorator

    def prange(*args, **kwargs):
        """Fallback de `numba.prange`: equivalente a `range()` en Python
        puro (la paralelizacion solo aplica si Numba esta instalado)."""
        return range(*args, **kwargs)
