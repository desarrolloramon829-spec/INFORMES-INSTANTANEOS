---
name: plan-comparativo-dos-periodos
description: "Usar cuando se necesite diseñar o refinar un requerimiento de comparativo entre dos rangos de fechas en la app de informes del mapa delictual. Genera un plan técnico alineado con la estructura actual de loader, engine, charts y páginas Streamlit."
argument-hint: "Describí los dos periodos a comparar, las métricas esperadas y si querés una nueva página o extender la existente"
---

Objetivo: crear un plan de implementación para un comparativo entre dos periodos de fechas en este sistema.

Contexto del proyecto:
- La app ya tiene una página de comparativo anual en app/src/ui/pages/comparativo.py.
- Los datos ya exponen _fecha y _anio desde app/src/data/loader.py.
- Los filtros globales ya soportan rango de fechas en app/src/ui/shared.py.
- La lógica estadística actual vive en app/src/stats/engine.py.
- Los gráficos comparativos actuales viven en app/src/charts/generator.py.

Instrucciones:
1. Analizá el requerimiento pedido por el usuario y reformulalo como objetivo funcional.
2. Detectá si conviene:
   - extender la página comparativo existente, o
   - crear una nueva vista específica para comparación entre periodos.
3. Proponé un plan por etapas, usando exactamente estas secciones:
   - Alcance funcional
   - Cambios de backend y datos
   - Cambios de lógica estadística
   - Cambios de interfaz
   - Validaciones y casos borde
   - Pruebas recomendadas
   - Riesgos y decisiones pendientes
4. En Cambios de lógica estadística, considerar explícitamente:
   - filtrado por fecha desde _fecha
   - comparación entre periodo A y periodo B
   - diferencia absoluta
   - variación porcentual
   - tratamiento cuando el periodo base tiene cero registros
   - reutilización o extensión de comparativo_periodos y comparativo_mensual
5. En Cambios de interfaz, considerar explícitamente:
   - dos selectores de rango independientes
   - validación de periodos solapados o invertidos
   - métricas resumen
   - tabla comparativa
   - gráficos comparativos
   - exportación CSV
6. Basate en la estructura real del repositorio. Mencioná archivos concretos cuando corresponda.
7. No escribas código salvo que el usuario lo pida. Entregá un plan técnico accionable.

Formato de salida:
- Redactá en español.
- Sé específico con archivos y responsabilidades.
- Si faltan decisiones, cerrá con una lista breve de preguntas.

Entrada del usuario:
{{input}}
