# MVP del TFG (JFLAP en Python)

## Objetivo del MVP
Construir una aplicación de escritorio en Python para crear y simular autómatas finitos (AFD/AFND), con una interfaz gráfica usable y operaciones básicas, reutilizando el núcleo algorítmico ya implementado en el proyecto.

## Definición de éxito (entregable mínimo)
El MVP está completado si se cumplen **todos** estos puntos:

1. Se puede crear un autómata visualmente (estados y transiciones).
2. Se puede marcar estado inicial y estados finales.
3. Se puede simular una palabra y mostrar si pertenece o no al lenguaje.
4. Se puede guardar/cargar en el formato de texto del proyecto.
5. Se puede ejecutar al menos 3 operaciones automáticas desde la UI (por ejemplo: determinización, complemento, minimización).
6. Hay validación de errores de entrada y mensajes claros al usuario.
7. Hay una demo reproducible y documentación mínima de uso.

## Alcance funcional del MVP

### Incluido (must-have)
- Editor gráfico básico:
  - Añadir/eliminar estado.
  - Añadir/eliminar transición.
  - Mover estados en el canvas.
  - Marcar inicial/final.
- Simulación:
  - Entrada de palabra.
  - Resultado de aceptación/rechazo.
  - Vista paso a paso opcional simple (texto de estados visitados).
- Persistencia:
  - Importar desde archivo de autómata existente.
  - Exportar al mismo formato.
- Operaciones sobre autómatas (con backend actual):
  - Determinización.
  - Complementario.
  - Minimización.
- Calidad mínima:
  - Manejo de errores en archivos mal formados.
  - Pruebas básicas de regresión de operaciones clave.

### Excluido (para fase 2)
- Asistente IA / lenguaje natural.
- Modo ejercicios autoevaluables.
- Soporte completo de PDA/gramáticas en la misma UI.
- Animaciones complejas y colaboración en tiempo real.

## Arquitectura recomendada (simple y viable)
- **Núcleo**: clases actuales (`AFND.py`, etc.) sin reescribir la lógica principal.
- **Adaptador**: capa intermedia para convertir datos entre UI y modelo interno.
- **UI**: desktop Python (PySide6 o Tkinter; PySide6 da mejor UX visual).
- **Persistencia**: lector/escritor actual de archivos de autómatas.

## Roadmap hasta mediados de junio

### Marzo (fundación)
- Semana 1-2:
  - Elegir framework UI y crear estructura del proyecto GUI.
  - Definir modelo de datos visual (posición de nodos + metadatos).
- Semana 3-4:
  - Canvas con estados/transiciones.
  - Crear, seleccionar, borrar, mover estados.
  - Marcar inicial/final.

### Abril (funcionalidad principal)
- Semana 5-6:
  - Integrar carga/guardado con formato actual.
  - Simulación de palabra (acepta/rechaza).
- Semana 7-8:
  - Integrar determinización y complementario desde la UI.
  - Mostrar resultado en nuevo panel o reemplazo de autómata.

### Mayo (operaciones + calidad)
- Semana 9-10:
  - Integrar minimización.
  - Validaciones y mensajes de error.
- Semana 11-12:
  - Pruebas funcionales (casos de ejemplo del proyecto).
  - Pulido UX, consistencia visual, atajos básicos.

### Junio (cierre)
- Semana 13:
  - Documentación final de usuario y técnica.
  - Demo guiada (script de 5-10 min).
- Semana 14:
  - Correcciones finales y preparación de defensa.

## Riesgos y mitigación
- Riesgo: sobrealcance de funcionalidades.
  - Mitigación: congelar alcance del MVP al final de abril.
- Riesgo: UI consume más tiempo de lo esperado.
  - Mitigación: priorizar interacción básica sobre estética avanzada.
- Riesgo: integración entre UI y backend.
  - Mitigación: crear adaptador y tests de integración tempranos.

## Checklist semanal de control
- ¿Se cerró al menos 1 funcionalidad visible al usuario esta semana?
- ¿Se añadieron o actualizaron pruebas de regresión?
- ¿La demo sigue funcionando de extremo a extremo?
- ¿Se mantiene el alcance MVP sin añadir extras no planificados?

## Criterio de "listo para entregar"
- Flujo completo en vivo: crear autómata -> simular palabra -> aplicar operación -> guardar/cargar.
- Sin errores críticos en demo.
- Memoria documenta objetivos, diseño, pruebas y resultados.
