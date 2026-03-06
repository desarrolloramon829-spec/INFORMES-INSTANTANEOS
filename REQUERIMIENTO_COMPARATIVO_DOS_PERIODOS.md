# Requerimiento Formal - Comparativo Entre Dos Periodos

## Objetivo

Incorporar en la página de comparativo de la aplicación la posibilidad de comparar dos rangos de fechas arbitrarios, por ejemplo del 01/02 al 07/02 versus del 08/02 al 14/02, manteniendo los filtros globales ya existentes de unidad regional, comisaría, tipo de delito y modus operandi.

## Alcance funcional

- El comparativo convivirá con el modo actual de comparación por años.
- La funcionalidad se implementará dentro de la página existente de comparativo y no como una pantalla separada.
- El usuario podrá definir dos periodos independientes:
  - Periodo A, tomado como base.
  - Periodo B, tomado como comparación.
- El sistema mostrará:
  - total de registros del Periodo A
  - total de registros del Periodo B
  - diferencia absoluta entre ambos
  - variación porcentual de B respecto de A
  - comparación por delito
  - tabla comparativa por comisaría entre ambos periodos
  - comparación por otras dimensiones configurables
  - evolución diaria alineada por posición dentro del rango
  - exportación de resultados en CSV

## Cambios de backend y datos

- Se reutiliza la columna \_fecha ya generada por la carga de datos.
- No se requiere modificar la lectura de shapefiles.
- La nueva lógica se implementa sobre el motor estadístico actual para evitar duplicación.

## Cambios de lógica estadística

- Se agrega comparación entre dos rangos de fechas inclusivos.
- La comparación usa esta convención:
  - diferencia = total Periodo B menos total Periodo A
  - porcentaje = variación de B respecto de A
- Se agrega una tabla específica por comisaría o jurisdicción, comparando los totales de hechos de la misma dependencia entre ambos periodos.
- La tabla por comisaría debe agrupar por JURIS_HECH o por la etiqueta visible de comisaría utilizada en la interfaz, manteniendo consistencia con los filtros actuales.
- Cada fila de la tabla por comisaría debe incluir:
  - nombre de la comisaría
  - total del Periodo A
  - total del Periodo B
  - diferencia absoluta
  - variación porcentual
- Ejemplo esperado:
  - Cria 1 | 01/03 al 07/03 = 10 | 08/03 al 14/03 = 11 | diferencia = +1
- Regla de variación porcentual cuando el Periodo A tiene cero registros:
  - si B también tiene cero, la variación es 0
  - si B tiene registros y A es cero, la variación se informa como 100.0 por convención del sistema, para mantener consistencia con el comparativo anual existente
- La evolución diaria se alinea por posición relativa dentro del rango:
  - Día 1 contra Día 1
  - Día 2 contra Día 2
  - y así sucesivamente
- Si los periodos tienen distinta duración:
  - la comparación sigue habilitada
  - se informa visualmente que la duración es distinta
  - la evolución diaria se muestra hasta la longitud mayor, completando implícitamente con cero cuando uno de los periodos no tiene un día equivalente

## Cambios de interfaz

- La página comparativo tendrá dos modos:
  - Años
  - Rangos de fechas
- En modo rangos de fechas se mostrarán cuatro selectores:
  - Desde A
  - Hasta A
  - Desde B
  - Hasta B
- Validaciones de interfaz:
  - si una fecha desde es mayor que su fecha hasta, el comparativo no se ejecuta
  - si los periodos se solapan, el comparativo sigue disponible pero se muestra advertencia
  - si las duraciones son distintas, se informa al usuario con mensaje explicativo
- La pantalla incluirá:
  - métricas resumen
  - gráfico de evolución diaria
  - gráfico comparativo por delito
  - tabla comparativa por comisaría
  - tabla detallada por dimensión
  - descarga CSV de evolución diaria y tabla detallada

## Validaciones y casos borde

- Conjunto filtrado sin fechas válidas: la pantalla debe informar que no es posible comparar por rangos.
- Periodos solapados: se advierte pero no se bloquea.
- Periodos de distinta longitud: se advierte pero no se bloquea.
- Periodo con cero registros: se debe mostrar la tabla y los indicadores sin fallar.
- Filtros muy restrictivos: se debe permitir exportar aun si el resultado es reducido.
- Comisarías presentes en un periodo y ausentes en el otro: deben aparecer igual en la tabla con valor 0 en el periodo faltante.

## Pruebas recomendadas

- Comparación de dos semanas consecutivas del mismo mes.
- Comparación de dos periodos del mismo largo en meses distintos.
- Comparación de periodos de distinto largo.
- Comparación con solapamiento parcial.
- Comparación bajo una sola unidad regional.
- Comparación bajo una sola comisaría.
- Verificación de tabla por comisaría con varias dependencias y con dependencias sin registros en uno de los dos periodos.
- Exportación CSV con resultados vacíos o parciales.

## Riesgos y decisiones cerradas

- Se decidió extender la página existente en lugar de crear una nueva.
- Se decidió permitir periodos solapados con advertencia.
- Se decidió permitir periodos de distinta duración con advertencia.
- Se decidió alinear la evolución por posición relativa diaria y no por fecha calendario exacta.
- Se decidió mantener la convención de 100.0 cuando la base es cero y el periodo comparado sí tiene registros.
- Se decidió que la tabla por comisaría compare siempre la misma dependencia entre ambos rangos, aunque en uno de ellos no tenga registros.

## Referencias técnicas

- Página actual: app/src/ui/pages/comparativo.py
- Motor estadístico: app/src/stats/engine.py
- Filtros globales: app/src/ui/shared.py
- Fechas normalizadas: app/src/data/loader.py
- Prompt de planificación usado como base: .github/prompts/plan-comparativo-dos-periodos.prompt.md
