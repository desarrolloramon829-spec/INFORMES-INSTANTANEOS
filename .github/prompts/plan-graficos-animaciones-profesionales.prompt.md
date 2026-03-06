---
name: plan-graficos-animaciones-profesionales
description: "Usar cuando se necesite diseñar un plan profesional para mejorar gráficos, animaciones, transiciones y experiencia visual del sistema de informes del mapa delictual. Produce un plan técnico y visual aterrizado al código actual en Streamlit y Plotly."
argument-hint: "Describí el objetivo visual, las pantallas foco y el nivel de rediseño esperado"
agent: "agent"
---

Objetivo: crear un plan de mejora visual integral para este sistema, enfocado en gráficos, animaciones, jerarquía visual, consistencia de interfaz y experiencia de usuario.

Contexto del proyecto:
- La aplicación está construida con Streamlit.
- Los gráficos están centralizados en app/src/charts/generator.py.
- Las pantallas viven en app/src/ui/pages/.
- El sistema contiene dashboards comparativos, métricas, tablas y filtros laterales.
- El objetivo no es hacer un rediseño abstracto, sino un plan aplicable al código y a la estructura actual del repositorio.

Instrucciones:
1. Analizá el pedido del usuario y reformulalo como objetivo visual y técnico.
2. Basate en la estructura real del proyecto para proponer cambios concretos.
3. Generá un plan usando exactamente estas secciones:
   - Diagnóstico visual actual
   - Objetivo de diseño
   - Mejoras de gráficos
   - Mejoras de animación y transición
   - Mejoras de jerarquía visual y layout
   - Cambios técnicos por archivo
   - Roadmap por fases
   - Riesgos y validaciones
4. En Mejoras de gráficos, considerar explícitamente:
   - consistencia entre colores, tipografía y títulos
   - uso de gráficos apropiados por tipo de dato
   - reducción de ruido visual
   - mejoras en ejes, leyendas, tooltips y etiquetas
   - prioridades entre barras, líneas, donas, tablas y comparativos
5. En Mejoras de animación y transición, considerar explícitamente:
   - qué puede resolverse de forma nativa con Plotly
   - qué puede resolverse con Streamlit sin romper rendimiento
   - transiciones entre estados, tabs, filtros y comparativos
   - límites prácticos para no degradar la experiencia
6. En Cambios técnicos por archivo, mencionar rutas concretas del repositorio cuando corresponda.
7. No escribas código salvo que el usuario lo pida. Entregá un plan accionable, priorizado y realista.

Formato de salida:
- Redactá en español.
- Sé específico y orientado a implementación.
- Evitá ideas genéricas de diseño sin impacto técnico concreto.
- Cerrá con una lista breve de decisiones abiertas si hubiera ambigüedades.

Entrada del usuario:
{{input}}
