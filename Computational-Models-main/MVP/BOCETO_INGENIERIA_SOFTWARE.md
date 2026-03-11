# Boceto de Ingeniería del Software (TFG)

## 1. Contexto del sistema
Aplicación de escritorio en Python para crear, visualizar y operar con autómatas finitos (AFD/AFND), orientada a aprendizaje y experimentación en teoría de autómatas.

## 2. Objetivo del sistema
Permitir al usuario construir autómatas de forma visual, simular cadenas y aplicar operaciones clásicas (determinización, minimización, complemento, unión/intersección), con persistencia en archivos de texto compatibles con el proyecto.

## 3. Alcance
### Incluido (MVP)
- Editor visual de estados y transiciones.
- Marcado de estado inicial y estados finales.
- Simulación de pertenencia de palabra.
- Carga/guardado de autómatas en formato del proyecto.
- Operaciones básicas sobre autómatas desde UI.

### Excluido (fases posteriores)
- Asistente IA en lenguaje natural.
- Modo ejercicios autoevaluables.
- Colaboración multiusuario.

## 4. Actores
- **Usuario estudiante**: crea autómatas, simula palabras y aplica operaciones.
- **Usuario docente**: prepara ejemplos, valida resultados y demuestra conceptos.
- **Sistema de ficheros**: fuente/destino de archivos de autómatas.

## 5. Requisitos funcionales (RF)
- **RF01**: Crear y eliminar estados.
- **RF02**: Crear y eliminar transiciones etiquetadas.
- **RF03**: Marcar/desmarcar estado inicial y final.
- **RF04**: Simular una palabra y mostrar aceptación/rechazo.
- **RF05**: Determinizar autómatas no deterministas.
- **RF06**: Obtener autómata complementario.
- **RF07**: Minimizar autómata determinista.
- **RF08**: Calcular unión e intersección de dos autómatas.
- **RF09**: Cargar autómata desde archivo.
- **RF10**: Guardar autómata en archivo.

## 6. Requisitos no funcionales (RNF)
- **RNF01 (Usabilidad)**: operaciones principales en <= 3 clics desde menús/toolbar.
- **RNF02 (Rendimiento)**: respuesta < 2 s para autómatas de hasta 100 estados.
- **RNF03 (Portabilidad)**: ejecución en Windows (objetivo MVP), extensible a Linux.
- **RNF04 (Fiabilidad)**: validación de entrada y mensajes de error claros.
- **RNF05 (Mantenibilidad)**: separación lógica núcleo/UI y modularidad.

## 7. Casos de uso (catálogo)
- **UC01** Crear autómata.
- **UC02** Editar autómata (estados/transiciones).
- **UC03** Simular palabra.
- **UC04** Determinizar autómata.
- **UC05** Minimizar autómata.
- **UC06** Obtener complementario.
- **UC07** Operar unión/intersección entre dos autómatas.
- **UC08** Guardar autómata.
- **UC09** Cargar autómata.
- **UC10** Ver diagrama de transición.

## 8. Especificación detallada de caso de uso (ejemplo)
### UC03 – Simular palabra
- **Actor principal**: Usuario estudiante.
- **Precondiciones**: existe un autómata válido cargado o creado.
- **Disparador**: el usuario introduce una palabra y pulsa “Simular”.
- **Flujo principal**:
  1. El usuario introduce la cadena.
  2. El sistema valida símbolos respecto al alfabeto.
  3. El sistema ejecuta el algoritmo de pertenencia.
  4. El sistema muestra resultado (acepta/rechaza) y traza de estados.
- **Flujos alternativos**:
  - A1: símbolo no válido -> mensaje de error y no se ejecuta simulación.
  - A2: autómata incompleto -> advertencia y sugerencia de corrección.
- **Postcondiciones**: se registra el resultado de la simulación en la vista actual.

## 9. Historias de usuario (boceto)
- Como estudiante, quiero dibujar un autómata, para comprobar visualmente su estructura.
- Como estudiante, quiero probar cadenas, para saber si pertenecen al lenguaje.
- Como estudiante, quiero minimizar un AFD, para comparar autómata original y reducido.
- Como docente, quiero cargar ejemplos desde archivo, para preparar clases más rápido.

## 10. Criterios de aceptación (ejemplos)
- **CA-RF04**: dada la palabra `011` en el autómata de ejemplo, el sistema devuelve “rechazada”.
- **CA-RF05**: al aplicar determinización a un AFND, el resultado cumple `deterministicAutomaton() == True`.
- **CA-RF09/RF10**: guardar y recargar preserva estados, alfabeto, transiciones, inicial y finales.

## 11. Modelo de datos (alto nivel)
- **Automaton**: states, alphabet, transitions, initial_state, final_states.
- **Transition**: start_state, symbol, end_states.
- **Project/UIState**: layout de nodos (posición x,y), selección y zoom.

## 12. Arquitectura propuesta (alto nivel)
- **Capa dominio**: lógica formal ya existente (`AFND.py`, `AFND_nullable.py`, etc.).
- **Capa aplicación**: servicios/casos de uso que orquestan llamadas al dominio.
- **Capa presentación**: interfaz gráfica (canvas, panel de propiedades, simulación).
- **Infraestructura**: lectura/escritura de archivos, logs y configuración.

## 13. Plan de iteraciones (marzo-junio)
- **Iteración 1 (marzo)**: editor gráfico básico + creación/edición.
- **Iteración 2 (abril)**: simulación + carga/guardado.
- **Iteración 3 (mayo)**: operaciones automáticas + validaciones.
- **Iteración 4 (junio)**: pruebas, documentación y demo final.

## 14. Riesgos y mitigación
- **R1**: sobrecarga de funcionalidades -> congelar alcance MVP al final de abril.
- **R2**: problemas de integración UI/dominio -> diseñar adaptadores desde el inicio.
- **R3**: tiempos cortos de pruebas -> reservar mínimo 2 semanas de cierre.

## 15. Estrategia de pruebas (resumen)
- **Unitarias**: métodos de dominio (pertenencia, determinización, minimización).
- **Integración**: UI -> servicio -> dominio.
- **Aceptación**: escenarios reales de clase (casos de uso UC03, UC04, UC05, UC09).

## 16. Trazabilidad básica
- RF04 -> UC03 -> Prueba Aceptación TA03.
- RF05 -> UC04 -> Prueba Aceptación TA04.
- RF07 -> UC05 -> Prueba Aceptación TA05.
- RF09/RF10 -> UC08/UC09 -> Prueba Aceptación TA08/TA09.

---

## Nota para memoria del TFG
Este documento es un boceto inicial. En la memoria final conviene añadir:
- Diagrama de casos de uso UML.
- Diagrama de clases simplificado.
- Prototipos de interfaz.
- Métricas de pruebas y resultados experimentales.
