# Instrucciones para agentes

Este repositorio usa **[CLAUDE.md](CLAUDE.md)** como documento de instrucciones. **Leelo
primero**: contiene la terminología obligatoria, los comandos, las reglas duras y una
tabla que indica qué capítulo de [docs/convenciones/](docs/convenciones/) leer según lo que
vayas a tocar.

Orden recomendado al llegar:

1. [CLAUDE.md](CLAUDE.md) — reglas duras y ruteo.
2. [docs/notas/ESTADO.md](docs/notas/ESTADO.md) — qué está en curso ahora mismo.
3. [docs/MAPA.md](docs/MAPA.md) — estructura del repo y **rutas frágiles que no se pueden mover**.
4. El capítulo de [docs/convenciones/](docs/convenciones/) que corresponda a tu tarea.
5. [docs/convenciones/no-reintroducir.md](docs/convenciones/no-reintroducir.md) — antes de
   agregar algo que parece faltar.

Tres cosas que suelen sorprender:

- **Todo lo visible al usuario va en español**, con terminología fija (GDL, MEF, restricción,
  tensión…). La tabla canónica está en `CLAUDE.md`.
- **Cero colores hexadecimales fuera de `config/settings.py`.** La auditoría previa a
  integrar espera 0 coincidencias en `gui/` y `education/`.
- **Muchas ausencias son decisiones tomadas**, no olvidos: no hay toolbar, no hay menú
  *Ver*, los módulos no tienen botón de cerrar propio. Está todo documentado.

Las notas de trabajo van en [docs/notas/](docs/notas/), no en este archivo ni en `CLAUDE.md`.
