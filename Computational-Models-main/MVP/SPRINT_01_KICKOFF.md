# Sprint 1 (Kickoff) — MVP JFLAP en Python

## Decisión técnica inicial
- Framework UI: **PySide6** (mejor base para editor visual en canvas que Tkinter).
- Núcleo algorítmico: reutilizar clases existentes (`AFND.py`, `TransitionFunction.py`, etc.).
- Estrategia: construir primero un flujo mínimo extremo a extremo y luego ampliar.

## Objetivo del sprint (1 semana)
Tener una aplicación mínima que abra ventana, permita crear estados en un canvas, marcar inicial/final y exportar/importar un autómata simple.

## Entregables de Sprint 1
1. Estructura de proyecto GUI creada.
2. Ventana principal + canvas funcional.
3. Alta/baja de estados desde UI.
4. Marcado de estado inicial y final.
5. Guardado y carga básica en formato de autómata del proyecto.
6. Demo reproducible en menos de 2 minutos.

## Backlog técnico (ordenado)

### Tarea S1-01 — Estructura base GUI
- Crear módulos:
  - `app/main.py`
  - `app/ui/main_window.py`
  - `app/ui/canvas_view.py`
  - `app/domain/automaton_adapter.py`
  - `app/services/io_service.py`
- Criterio de hecho:
  - La app arranca sin errores y muestra ventana vacía.

### Tarea S1-02 — Modelo visual mínimo
- Definir representación visual:
  - nodo: `id`, `x`, `y`, `is_initial`, `is_final`
  - transición: `from_state`, `symbol`, `to_states`
- Criterio de hecho:
  - Se pueden crear nodos con click en canvas.

### Tarea S1-03 — Operaciones básicas de estados
- Crear, seleccionar, mover, eliminar estado.
- Toggle inicial/final desde menú contextual o panel lateral.
- Criterio de hecho:
  - Siempre existe como máximo 1 estado inicial.

### Tarea S1-04 — Guardar/Cargar
- Convertir modelo visual <-> formato de archivo actual.
- Guardado a `.txt` compatible con `FiniteAutomaton.readAutomaton(...)`.
- Criterio de hecho:
  - Guardar y recargar conserva estados y propiedades inicial/final.

### Tarea S1-05 — Demo y validación
- Escenario demo:
  1. Crear 2 estados.
  2. Marcar inicial/final.
  3. Guardar archivo.
  4. Cargar archivo.
- Criterio de hecho:
  - Sin errores críticos en ejecución.

## Riesgos del sprint y mitigación
- Riesgo: atasco en UI/canvas.
  - Mitigación: empezar sin transiciones curvas ni edición avanzada.
- Riesgo: incompatibilidad de formato.
  - Mitigación: validar desde el primer día contra `readAutomaton`.

## Definición de Done del Sprint 1
- App ejecutable.
- Flujo crear/editar estado + guardar/cargar operativo.
- Evidencia: GIF/video corto + 3 capturas.
