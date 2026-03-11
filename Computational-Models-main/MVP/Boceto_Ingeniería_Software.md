Boceto de Ingenieria del Software

1. Que es la app
AutoSandbox es una aplicacion de escritorio para crear y probar automatas de forma visual.

2. Objetivo
Construir una app sencilla que permita:
- crear estados y transiciones,
- simular cadenas,
- aplicar operaciones basicas de automatas,
- guardar y cargar archivos.

3. Actores
- Estudiante: usa la app para practicar.
- Profesor: usa la app para explicar ejemplos.

4. Requisitos funcionales minimos
- RF1: Abrir la app y navegar entre pantallas.
- RF2: Entrar a la vista de automata finito.
- RF3: Arrastrar la herramienta circulo al lienzo.
- RF4: Dejar el estado en una posicion y moverlo despues.
- RF5: Volver al inicio con Back.

5. Requisitos no funcionales minimos
- RNF1: Interfaz clara y facil de usar.
- RNF2: Tiempo de respuesta inmediato en acciones basicas.
- RNF3: Estabilidad de la aplicación frente a errores.

6. Casos de uso basicos
- CU1: Entrar en "Finite Automaton".
- CU2: Crear un estado arrastrando un círculo al lienzo.
- CU3: Mover un estado existente.
- CU4: Volver al menu principal.

7. Arquitectura simple
- Capa visual (PySide6): ventanas, botones, lienzo.
- Capa logica: operaciones de automatas existentes del proyecto.
- Capa datos: lectura/escritura de archivos de automatas.