# PLAN DE DESARROLLO - APP INFORMES DEL MAPA DELICTUAL

## Versión: 1.0 | Fecha: 25/02/2026

---

## 1. RESUMEN EJECUTIVO

Aplicación de escritorio/web para la generación automatizada de informes estadísticos del mapa delictual de la Provincia de Tucumán. La app leerá archivos Shapefile (.shp) provenientes de QGIS 2.14.14 (Essen) y producirá reportes con gráficos estilo Power BI, tablas comparativas y dashboards interactivos.

---

## 2. ARQUITECTURA PROPUESTA

### 2.1 Stack Tecnológico

| Componente                   | Tecnología                          | Justificación                                                              |
| ---------------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| **Backend**                  | Python 3.10+                        | Ecosistema maduro para GIS (geopandas, fiona, shapely)                     |
| **Lectura Shapefiles**       | `geopandas` + `fiona` + `pyshp`     | Lectura nativa de .shp/.dbf/.shx                                           |
| **Frontend/UI**              | Streamlit o Dash (Plotly)           | Dashboards interactivos estilo Power BI sin necesidad de frontend separado |
| **Gráficos**                 | Plotly + Matplotlib/Seaborn         | Gráficos interactivos de alta calidad                                      |
| **Exportación**              | `openpyxl` + `reportlab` + `pdfkit` | Exportar a Excel y PDF                                                     |
| **Base de datos (opcional)** | SQLite / PostgreSQL+PostGIS         | Caché local de datos procesados                                            |
| **Empaquetado**              | PyInstaller / Docker                | Distribución como .exe o contenedor                                        |

### 2.2 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Dashboard   │  │  Filtros de  │  │  Exportación  │  │
│  │  Interactivo │  │  Fecha/Zona  │  │  PDF / Excel  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────┤
│                   CAPA DE LÓGICA DE NEGOCIO              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Motor de    │  │  Generador   │  │  Comparador   │  │
│  │  Estadísticas│  │  de Gráficos │  │  de Períodos  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│                   CAPA DE DATOS                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Lector de   │  │  Normalizador│  │  Caché/DB    │  │
│  │  Shapefiles  │  │  de Datos    │  │  Local       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│              FUENTES DE DATOS (.shp en Z:\)              │
│  URC (15 Comisarías) │ URN (22) │ URO (20) │           │
│  URE (44 Comisarías) │ URS (27) │ FINCAS │ ABIGEATO   │
└─────────────────────────────────────────────────────────┘
```

---

## 3. FUENTES DE DATOS - SHAPEFILES

### 3.1 Ruta Base

```
Z:\MAPA DEL DELITO\MAPAS DEL DELITO POR JURISDICCIONES\
```

### 3.2 Catálogo de Shapefiles por Unidad Regional

#### Shapes Especiales

| #   | Nombre         | Ruta                                                                          |
| --- | -------------- | ----------------------------------------------------------------------------- |
| 1   | CARGA FINCAS   | `CARGA FINCAS - copia1\CARGA FINCAS Copia1\CARGA FINCAS Copia1.shp`           |
| 2   | CARGA ABIGEATO | `CARGA ABIGEATO - copia1\CARGA ABIGEATO - copia1\CARGA ABIGEATO - copia1.shp` |

#### Unidad Regional Este (URE) - 44 Comisarías

| #   | Comisaría            | Archivo .shp                                       |
| --- | -------------------- | -------------------------------------------------- |
| 1   | Burruyacu            | `MAPA DELICTUAL CRIA BURRUYACU-URE.shp`            |
| 2   | El Cajón             | `MAPA DELICTUAL CRIA EL CAJON-URE.shp`             |
| 3   | Villa Benjamín Aráoz | `MAPA DELICTUAL CRIA VILLA BENJAMIN ARAOZ-URE.shp` |
| 4   | El Puestito          | `MAPA DELICTUAL CRIA EL PUESTITO-URE.shp`          |
| 5   | Chilcas              | `MAPA DELICTUAL CRIA CHILCAS-URE.shp`              |
| 6   | 7 de Abril           | `MAPA DELICTUAL CRIA 7 DE ABRIL-URE.shp`           |
| 7   | El Chañar            | `MAPA DELICTUAL CRIA EL CHAÑAR-URE.shp`            |
| 8   | La Ramada            | `MAPA DELICTUAL CRIA LA RAMADA-URE.shp`            |
| 9   | Garmendia            | `MAPA DELICTUAL CRIA GARMENDIA-URE.shp`            |
| 10  | El Timbó             | `MAPA DELICTUAL CRIA EL TIMBO-URE.shp`             |
| 11  | El Naranjo           | `MAPA DELICTUAL CRIA EL NARANJO-URE.shp`           |
| 12  | Gob. Piedrabuena     | `MAPA DELICTUAL CRIA GOB PIEDRABUENA-URE.shp`      |
| 13  | Villa Padre Monti    | `MAPA DELICTUAL CRIA VILLA PADRE MONTI-URE.shp`    |
| 14  | Banda del Río Salí   | `MAPA DELICTUAL CRIA BANDA DEL RIO SALI - URE.shp` |
| 15  | Lastenia             | `MAPA DELICTUAL CRIA LASTENIA - URE.shp`           |
| 16  | Güemes               | `MAPA DELICTUAL CRIA GUEMES-URE-2020.shp`          |
| 17  | Alderetes            | `MAPA DELICTUAL CRIA ALDERETES-URE.shp`            |
| 18  | Pozo del Alto        | `MAPA DELICTUAL CRIA POZO DEL ALTO-URE.shp`        |
| 19  | Ranchillos           | `MAPA DELICTUAL CRIA DE RANCHILLOS-URE.shp`        |
| 20  | Los Ralos            | `MAPA DELICTUAL CRIA LOS RALOS-URE.shp`            |
| 21  | Delfín Gallo         | `MAPA DELICTUAL CRIA DELFIN GALLO-URE.shp`         |
| 22  | Colombres            | `MAPA DELICTUAL CRIA COLOMBRES-URE.shp`            |
| 23  | La Florida           | `MAPA DELICTUAL CRIA LA FLORIDA-URE.shp`           |
| 24  | San Andrés           | `MAPA DELICTUAL CRIA SAN ANDRES-URE.shp`           |
| 25  | El Bracho            | `MAPA DELICTUAL CRIA EL BRACHO-URE.shp`            |
| 26  | Las Cejas            | `MAPA DELICTUAL CRIA LAS CEJAS-URE.shp`            |
| 27  | Los Bulacios         | `MAPA DELICTUAL CRIA LOS BULACIOS-URE.shp`         |
| 28  | Bella Vista          | `MAPA DELICTUAL CRIA BELLA VISTA-URE.shp`          |
| 29  | Romera Pozo          | `MAPA DELICTUAL CRIA ROMERA POZO-URE.shp`          |
| 30  | Santa Rosa de Leales | `MAPA DELICTUAL CRIA SANTA ROSA DE LEALES-URE.shp` |
| 31  | Quilmes              | `MAPA DELICTUAL CRIA QUILMES-URE.shp`              |
| 32  | Ingenio Leales       | `MAPA DELICTUAL CRIA INGENIO LEALES-URE.shp`       |
| 33  | Los Sueldos          | `MAPA DELICTUAL CRIA LOS SUELDOS-URE.shp`          |
| 34  | Estación Aráoz       | `MAPA DELICTUAL CRIA ESTACION ARAOZ-URE.shp`       |
| 35  | Villa de Leales      | `MAPA DELICTUAL CRIA VILLA DE LEALES-URE.shp`      |
| 36  | Río Colorado         | `MAPA DELICTUAL CRIA RIO COLORADO-URE.shp`         |
| 37  | Esquina              | `MAPA DELICTUAL CRIA ESQUINA-URE.shp`              |
| 38  | Mancopa              | `MAPA DELICTUAL CRIA MANCOPA - URE.shp`            |
| 39  | Agua Dulce           | `MAPA DELICTUAL CRIA AGUA DULCE-URE.shp`           |
| 40  | Los Gomes            | `MAPA DELICTUAL CRIA LOS GOMES-URE.shp`            |
| 41  | Los Puestos          | `MAPA DELICTUAL CRIA LOS PUESTOS-URE.shp`          |
| 42  | Los Herrera          | `MAPA DELICTUAL CRIA LOS HERRERA-URE.shp`          |
| 43  | El Mojón             | `MAPA DELICTUAL CRIA EL MOJON-URE.shp`             |
| 44  | Campo Quimil         | `MAPA DELICTUAL CRIA CAMPO QUIMIL-URE.shp`         |

#### Unidad Regional Oeste (URO) - 20 Comisarías

| #   | Comisaría                    | Archivo .shp                                               |
| --- | ---------------------------- | ---------------------------------------------------------- |
| 1   | Tafí del Valle               | `MAPA DELICTUAL CRIA TAFI DEL VALLE-URO.shp`               |
| 2   | El Mollar                    | `MAPA DELICTUAL CRIA EL MOLLAR-URO.shp`                    |
| 3   | Amaicha del Valle            | `MAPA DELICTUAL CRIA AMAICHA DEL VALLE-URO.shp`            |
| 4   | Colalao del Valle            | `MAPA DELICTUAL CRIA COLALAO DEL VALLE-URO.shp`            |
| 5   | Lules                        | `MAPA DELICTUAL CRIA LULES-URO.shp`                        |
| 6   | La Reducción                 | `MAPA DELICTUAL CRIA LA REDUCCION-URO.shp`                 |
| 7   | El Manantial                 | `MAPA DELICTUAL CRIA EL MANANTIAL-URO.shp`                 |
| 8   | San Pablo                    | `MAPA DELICTUAL CRIA SAN PABLO-URO-2020.shp`               |
| 9   | Villa Nougués                | `MAPA DELICTUAL CRIA VILLA NOUGUES-URO.shp`                |
| 10  | Los Aguirre                  | `MAPA DELICTUAL CRIA LOS AGUIRRE-URO-2020.shp`             |
| 11  | Famaillá                     | `MAPA DELICTUAL CRIA FAMAILLA-URO.shp`                     |
| 12  | Teniente Berdina             | `MAPA DELICTUAL CRIA TENIENTE BERDINA-URO.shp`             |
| 13  | Monteros                     | `MAPA DELICTUAL CRIA MONTEROS-URO.shp`                     |
| 14  | Santa Lucía                  | `MAPA DELICTUAL CRIA SANTA LUCIA-URO.shp`                  |
| 15  | Acheral                      | `MAPA DELICTUAL CRIA ACHERAL-URO.shp`                      |
| 16  | Río Seco                     | `MAPA DELICTUAL CRIA RIO SECO-URO.shp`                     |
| 17  | Villa Quinteros              | `MAPA DELICTUAL CRIA VILLA QUINTEROS-URO.shp`              |
| 18  | León Rougés                  | `MAPA DELICTUAL CRIA LEON ROUGES-URO.shp`                  |
| 19  | Capitán Cáceres              | `MAPA DELICTUAL CRIA CAPITAN CACERES-URO.shp`              |
| 20  | Los Sosa y Soldado Maldonado | `MAPA DELICTUAL CRIA LOS SOSA Y SOLDADO MALDONADO-URO.shp` |
| 21  | Amberes                      | `MAPA DELICTUAL CRIA AMBERES-URO.shp`                      |
| 22  | Sargento Moya                | `MAPA DELICTUAL CRIA SARGENTO MOYA-URO.shp`                |

#### Unidad Regional Sur (URS) - 27 Comisarías

| #   | Comisaría              | Archivo .shp                                          |
| --- | ---------------------- | ----------------------------------------------------- |
| 1   | Concepción             | `MAPA DELICTUAL CRIA CONCEPCION-URS.shp`              |
| 2   | Alto Verde             | `CRIA ALTO VERDE-URS.shp`                             |
| 3   | Arcadia                | `MAPA DELICTUAL CRIA ARCADIA-URS.shp`                 |
| 4   | Alpachiri              | `MAPA DELICTUAL CRIA ALPACHIRI URS.shp`               |
| 5   | Medinas                | `MAPA DELICTUAL CRIA MEDINAS URS.shp`                 |
| 6   | La Trinidad            | `MAPA DELICTUAL CRIA LA TRINIDAD-URS.shp`             |
| 7   | Aguilares              | `MAPA DELICTUAL CRIA AGUILARES-URS.shp`               |
| 8   | Destacamento El Polear | `MAPA DELICTUAL DESTACAMENTO EL POLEAR URS.shp`       |
| 9   | Santa Ana              | `MAPA DELICTUAL CRIA SANTA ANA-URS.shp`               |
| 10  | Los Sarmientos         | `MAPA DELICTUAL CRIA LOS SARMIENTOS-URS.shp`          |
| 11  | Santa Cruz y La Tuna   | `MAPA DELICTUAL CRIA DE SANTA CRUZ Y LA TUNA-URS.shp` |
| 12  | Monteagudo             | `MAPA DELICTUAL CRIA DE MONTEAGUDO-URS.shp`           |
| 13  | Villa de Chicligasta   | `MAPA DELICTUAL CRIA DE VILLA DE CHICLIGASTA-URS.shp` |
| 14  | Graneros               | `MAPA DELICTUAL CRIA GRANEROS-URS.shp`                |
| 15  | Atahona                | `MAPA DELICTUAL CRIA ATAHONA-URS.shp`                 |
| 16  | Simoca                 | `MAPA DELICTUAL CRIA SIMOCA-URS.shp`                  |
| 17  | Taco Ralo              | `MAPA DELICTUAL CRIA DE TACO RALO-URS.shp`            |
| 18  | Villa Belgrano         | `MAPA DELICTUAL CRIA DE VILLA BELGRANO-URS.shp`       |
| 19  | Lamadrid               | `MAPA DELICTUAL CRIA DE LAMADRID-URS.shp`             |
| 20  | Alberdi                | `MAPA DELICTUAL CRIA ALBERDI-URS.shp`                 |
| 21  | Escaba                 | `MAPA DELICTUAL CRIA ESCABA-URS.shp`                  |
| 22  | La Invernada           | `MAPA DELICTUAL CRIA LA INVERNADA-URS.shp`            |
| 23  | La Cocha               | `MAPA DELICTUAL CRIA LA COCHA-URS.shp`                |
| 24  | San Ignacio            | `MAPA DELICTUAL CRIA SAN IGNACIO-URS.shp`             |
| 25  | Rumipunco              | `MAPA DELICTUAL CRIA RUMIPUNCO-URS.shp`               |
| 26  | Árboles Grandes        | `MAPA DELICTUAL CRIA ARBOLES GRANDES-URS.shp`         |
| 27  | Huasa Pampa            | `MAPA DELICTUAL CRIA DE HUASA PAMPA-URS.shp`          |

#### Unidad Regional Norte (URN) - 22 Comisarías

| #   | Comisaría             | Archivo .shp                                       |
| --- | --------------------- | -------------------------------------------------- |
| 1   | Trancas               | `MAPA DELICTUAL CRIA TRANCAS-URN.shp`              |
| 2   | Chuscha               | `MAPA DELICTUAL CRIA DE CHUSCHA.shp`               |
| 3   | Choromoro             | `MAPA DELICTUAL CRIA DE CHOROMORO.shp`             |
| 4   | Vipos                 | `MAPA DELICTUAL CRIA VIPOS-URN.shp`                |
| 5   | Subcomisaría de Tapia | `MAPA DELICTUAL SUBCOMISARIA DE TAPIA-URN.shp`     |
| 6   | San Pedro             | `MAPA DELICTUAL CRIA SAN PEDRO-URN.shp`            |
| 7   | Yerba Buena           | `MAPA DELICTUAL CRIA YERBA BUENA-URN.shp`          |
| 8   | Martí Coll            | `MAPA DELICTUAL CRIA MARTI COLL-URN.shp`           |
| 9   | San José              | `MAPA DELICTUAL CRIA SAN JOSE-URN-2020.shp`        |
| 10  | El Corte              | `MAPA DELICTUAL CRIA EL CORTE-URN.shp`             |
| 11  | San Javier            | `MAPA DELICTUAL CRIA SAN JAVIER-URN.shp`           |
| 12  | Villa Carmela         | `MAPA DELICTUAL CRIA VILLA CARMELA.shp`            |
| 13  | Raco                  | `MAPA DELICTUAL CRIA RACO-URN.shp`                 |
| 14  | Los Nogales           | `MAPA DELICTUAL CRIA LOS NOGALES-URN.shp`          |
| 15  | El Cadillal           | `MAPA DELICTUAL CRIA EL CADILLAL-URN.shp`          |
| 16  | Las Talitas           | `MAPA DELICTUAL CRIA LAS TALITAS-URN.shp`          |
| 17  | Villa Mariano Moreno  | `MAPA DELICTUAL CRIA VILLA MARIANO MORENO-URN.shp` |
| 18  | El Colmenar           | `MAPA DELICTUAL CRIA VILLA EL COLMENAR URN.shp`    |
| 19  | Los Pocitos           | `MAPA DELICTUAL CRIA LOS POCITOS-URN.shp`          |
| 20  | Lomas de Tafí         | `MAPA DELICTUAL CRIA LOMAS DE TAFI-URN.shp`        |
| 21  | Villa Obrera          | `MAPA DELICTUAL CRIA VILLA OBRERA-URN.shp`         |
| 22  | Tafí Viejo Centro     | `MAPA DELICTUAL CRIA TAFI VIEJO CENTRO-URN.shp`    |

#### Unidad Regional Capital (URC) - 15 Comisarías

| #   | Comisaría     | Archivo .shp                         |
| --- | ------------- | ------------------------------------ |
| 1   | Comisaría 1ª  | `MAPA DELICTUAL CRIA1-URC-2020.shp`  |
| 2   | Comisaría 2ª  | `MAPA DELICTUAL CRIA2-URC-2020.shp`  |
| 3   | Comisaría 3ª  | `MAPA DELICTUAL CRIA3-URC-2020.shp`  |
| 4   | Comisaría 4ª  | `MAPA DELICTUAL CRIA4-URC-2020.shp`  |
| 5   | Comisaría 5ª  | `MAPA DELICTUAL CRIA5-URC-2020.shp`  |
| 6   | Comisaría 6ª  | `MAPA DELICTUAL CRIA6-URC-2020.shp`  |
| 7   | Comisaría 7ª  | `MAPA DELICTUAL CRIA7-URC-2019.shp`  |
| 8   | Comisaría 8ª  | `MAPA DELICTUAL CRIA8-URC-2020.shp`  |
| 9   | Comisaría 9ª  | `MAPA DELICTUAL CRIA9-URC-2020.shp`  |
| 10  | Comisaría 10ª | `MAPA DELICTUAL CRIA10-URC-2020.shp` |
| 11  | Comisaría 11ª | `MAPA DELICTUAL CRIA11-URC-2020.shp` |
| 12  | Comisaría 12ª | `MAPA DELICTUAL CRIA12-URC-2020.shp` |
| 13  | Comisaría 13ª | `MAPA DELICTUAL CRIA13-URC-2020.shp` |
| 14  | Comisaría 14ª | `MAPA DELICTUAL CRIA14-URC-2020.shp` |
| 15  | Comisaría 15ª | `MAPA DELICTUAL CRIA15-URC-2020.shp` |

**Total de shapefiles: ~130 archivos**

---

## 4. MODELO DE DATOS

### 4.1 Campos Esperados en los Shapefiles (a validar con exploración real)

Basado en los reportes mostrados, los shapefiles deben contener campos similares a:

| Campo             | Tipo          | Descripción                        | Ejemplo                                        |
| ----------------- | ------------- | ---------------------------------- | ---------------------------------------------- |
| `DELITO`          | String        | Tipo de delito con modalidad       | `HURTO_OPORTUNISTA`, `ROBO_AGRAVADO_ASALTANTE` |
| `FECHA`           | Date/String   | Fecha del hecho                    | `2026-01-15`                                   |
| `HORA`            | String/Time   | Hora del hecho                     | `02:30`                                        |
| `FRANJA_HORARIA`  | String        | Franja horaria categorizada        | `MADRUGADA_(00:00-04:59)`                      |
| `DIA_SEMANA`      | String        | Día de la semana                   | `LUNES`, `MARTES`                              |
| `MES`             | String        | Mes del hecho                      | `ENERO`, `FEBRERO`                             |
| `MOVILIDAD`       | String        | Medio de movilidad del delincuente | `A_PIE`, `MOTOVEHICULO`, `#NO_CONSTA`          |
| `ARMA`            | String        | Tipo de arma utilizada             | `ARMA_DE_FUEGO`, `ARMA_BLANCA`                 |
| `AMBITO`          | String        | Ámbito de ocurrencia               | `VIVIENDA`, `VIA_PUBLICA`, `COMERCIO`          |
| `JURISDICCION`    | String        | Comisaría/Jurisdicción             | `COMISARIA 6ª`                                 |
| `UNIDAD_REGIONAL` | String        | Unidad Regional                    | `URC`, `URN`, `URO`, `URE`, `URS`              |
| `geometry`        | Point/Polygon | Geometría GIS                      | Coordenadas del hecho                          |

### 4.2 Catálogo de Valores por Campo

#### Franjas Horarias

```
MADRUGADA_(00:00-04:59)
MAÑANA_(05:00-08:59)
VESPERTINA_(09:00-12:59)
SIESTA_(13:00-16:59)
TARDE_(17:00-19:59)
NOCHE_(20:00-23:59)
```

#### Medios de Movilidad

```
#NO_CONSTA, A_PIE, MOTOVEHICULO, AUTOMOTOR, BICICLETA, #OTRO, SEMOVIENTE
```

#### Tipos de Armas

```
ARMA_DE_FUEGO, ARMA_BLANCA, OTRO_TIPO_DE_ARMA, ARMA_CASERA_TUMBERA,
REPLICA_DE_ARMA_DE_FUEGO, #NO_CONSTA, #NINGUNA, REPLICA_DE_ARMA_BLANCA
```

#### Ámbito de Ocurrencia

```
VIVIENDA, VIA_PUBLICA, COMERCIO, ESTABLECIMIENTO_EDUCATIVO_PRIVADO,
OBRAS_EN_CONSTRUCCION, ESTABLECIMIENTO_EDUCATIVO_PUBLICO,
ESTABLECIMIENTO_PRIVADO, LUGAR_DE_ESPARCIMIENTO, LUGAR_PUBLICO,
ESTABLECIMIENTO_PUBLICO, TRANSPORTE_PUBLICO_DE_PASAJEROS, EDIFICIO,
PREDIO, TRANSPORTE_OTROS, CAMPO, ESTABLECIMIENTO_PUBLICO_DE_SALUD,
BANCO, HOTEL, OFICINA, #OTRO, #NO_CONSTA,
ESTABLECIMIENTO_PRIVADO_DE_SALUD
```

#### Tipos de Delito (principales)

```
HURTO_OPORTUNISTA, ROBO_AGRAVADO_ASALTANTE, ROBO_ARREBATO,
ROBO_AGRAVADO_PIRAÑA_DE_MOTOVEHICULOS, ROBO_AGRAVADO_DE_AUTOMOTOR,
ROBO_AGRAVADO_ENTRADERA, ROBO_AGRAVADO_ARIETE,
ROBO_PIRAÑA_DE_MOTOVEHICULOS, ROBO_PIRAÑA, ROBO_OPORTUNISTA,
ROBO_DE_MOTOVEHICULOS, ROBO_CLAVERO_DE_AUTOS, ROBO_DE_AUTOMOTOR,
ROBO_AGRAVADO_ASALTANTE_EN_BANDA, ROBO_BOQUETERO, ROBO_ROMPE_VIDRIO,
ROBO_AGRAVADO_DE_MOTOVEHICULOS, HURTO_INHIBIDOR_ALARMA, HURTO_PUNGA,
HURTO_ESCALAMIENTO, HURTO_MECHERA, HURTO_MOTOVEHICULO, HURTO_AUTOMOTOR,
HURTO_VIUDA_NEGRA,
TENTATIVA_DE_ROBO_AGRAVADO_ASALTANTE_EN_BANDA, ...
ESTAFA_CUENTO_DEL_TIO, ESTAFA_TELEFONICA, ESTAFA_BANCARIA,
ESTAFA_SUPLANTACION_DE_IDENTIDAD, ESTAFA_CIBERNETICA_(PHISHING),
ESTAFA_INFORMATICA_(REDES_SOCIALES_ETC),
ESTAFA_CLONACION_DE_TARJETA_(SKIMMING), ESTAFA_FALSIFICACION_DE_MONEDA,
189_BIS
```

#### Unidades Regionales

```
UNIDAD_REGIONAL_CAPITAL (URC)
UNIDAD_REGIONAL_NORTE (URN)
UNIDAD_REGIONAL_OESTE (URO)
UNIDAD_REGIONAL_ESTE (URE)
UNIDAD_REGIONAL_SUR (URS)
```

---

## 5. MÓDULOS DE LA APLICACIÓN

### 5.1 Módulo 1: Carga y Normalización de Datos

**Responsabilidad**: Leer todos los shapefiles, unificar esquemas y crear un DataFrame consolidado.

```python
# Pseudocódigo
class ShapefileLoader:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.registry = self._load_shapefile_registry()

    def load_all(self, filter_ur=None) -> gpd.GeoDataFrame:
        """Carga todos los shapefiles o filtra por Unidad Regional"""

    def load_single(self, shapefile_path: str) -> gpd.GeoDataFrame:
        """Carga un shapefile individual"""

    def normalize_columns(self, gdf) -> gpd.GeoDataFrame:
        """Normaliza nombres de columnas entre diferentes shapes"""

    def validate_data(self, gdf) -> dict:
        """Valida integridad de datos y reporta problemas"""
```

**Tareas**:

- [ ] Explorar estructura real de cada shapefile (.dbf) para mapear campos
- [ ] Crear diccionario de mapeo de columnas (cada shape puede tener nombres diferentes)
- [ ] Manejar encoding (UTF-8, Latin1) de caracteres especiales (ñ, acentos)
- [ ] Derivar campos faltantes (ej: `FRANJA_HORARIA` a partir de `HORA`)
- [ ] Asignar `UNIDAD_REGIONAL` según la ruta del shapefile

### 5.2 Módulo 2: Motor de Estadísticas

**Responsabilidad**: Calcular todas las estadísticas requeridas para los informes.

```python
class StatsEngine:
    def __init__(self, data: gpd.GeoDataFrame):
        self.data = data

    def filter_by_date_range(self, start: date, end: date):
        """Filtra datos por rango de fechas"""

    def delitos_por_modalidad(self) -> pd.DataFrame:
        """Tabla: Delito | Período 1 | Período 2 | Diferencia | % Diferencia"""

    def delitos_por_dia_semana(self) -> pd.DataFrame:
        """Matriz: Delito x Día de semana con totales"""

    def delitos_por_franja_horaria(self) -> pd.DataFrame:
        """Matriz: Delito x Franja horaria con totales"""

    def medios_movilidad(self) -> pd.DataFrame:
        """Tabla con conteo y porcentaje por medio de movilidad"""

    def armas_utilizadas(self) -> pd.DataFrame:
        """Tabla con conteo y porcentaje por tipo de arma"""

    def ambito_ocurrencia(self) -> pd.DataFrame:
        """Tabla con conteo y porcentaje por ámbito"""

    def delitos_por_mes(self) -> pd.DataFrame:
        """Tabla con conteo y porcentaje por mes"""

    def delitos_por_jurisdiccion(self) -> pd.DataFrame:
        """Tabla con conteo y porcentaje por comisaría"""

    def delitos_por_unidad_regional(self) -> pd.DataFrame:
        """Tabla con conteo y porcentaje por unidad regional"""

    def comparativo_periodos(self, period1, period2) -> pd.DataFrame:
        """Tabla comparativa entre dos períodos con diferencias"""
```

### 5.3 Módulo 3: Generador de Gráficos (Estilo Power BI)

**Responsabilidad**: Crear gráficos interactivos con estilo profesional Power BI.

```python
class ChartGenerator:
    # Paleta de colores estilo institucional/Power BI
    COLORS = {
        'primary': '#2563EB',      # Azul
        'secondary': '#DC2626',    # Rojo
        'accent': '#F59E0B',       # Amarillo/Dorado
        'success': '#16A34A',      # Verde
        'purple': '#7C3AED',
        'orange': '#EA580C',
        'cyan': '#0891B2',
    }

    def bar_chart(self, data, title, x, y) -> plotly.Figure:
        """Gráfico de barras verticales con etiquetas de valor"""

    def stacked_bar(self, data, title) -> plotly.Figure:
        """Gráfico de barras apiladas (delito x día/franja)"""

    def comparative_bar(self, data, title) -> plotly.Figure:
        """Gráfico comparativo de dos períodos lado a lado"""

    def table_styled(self, data, title) -> plotly.Figure:
        """Tabla estilizada con colores condicionales"""

    def heatmap(self, data, title) -> plotly.Figure:
        """Mapa de calor (delito x franja horaria o día)"""

    def pie_chart(self, data, title) -> plotly.Figure:
        """Gráfico circular para distribuciones"""
```

### 5.4 Módulo 4: Dashboard Interactivo

**Responsabilidad**: Interfaz de usuario con filtros y navegación.

```
PANTALLAS DEL DASHBOARD:

1. 🏠 INICIO / RESUMEN GENERAL
   - KPIs principales (total delitos, variación %, top delito)
   - Mini-gráficos de tendencia
   - Selector de rango de fechas

2. 📊 DELITOS POR MODALIDAD
   - Tabla con tipos de delito y cantidades
   - Gráfico de barras horizontales
   - Filtro por Unidad Regional / Comisaría

3. 📅 ANÁLISIS TEMPORAL
   - Delitos por día de la semana (matriz + gráfico)
   - Delitos por franja horaria (matriz + gráfico)
   - Delitos por mes (tabla + gráfico)

4. 🔫 CARACTERÍSTICAS DEL HECHO
   - Medios de movilidad (tabla + gráfico)
   - Armas utilizadas (tabla + gráfico)
   - Ámbito de ocurrencia (tabla + gráfico)

5. 📍 ANÁLISIS GEOGRÁFICO
   - Delitos por jurisdicción/comisaría (tabla + gráfico)
   - Delitos por Unidad Regional (tabla + gráfico)
   - Mapa interactivo con puntos de delitos (usando Folium/Leaflet)

6. 📈 COMPARATIVO
   - Selector de dos rangos de fechas
   - Tabla comparativa con diferencias absolutas y porcentuales
   - Gráfico comparativo de barras agrupadas
   - Indicadores de suba/baja (flechas ↑↓)

7. 📋 EXPORTACIÓN
   - Generar informe PDF completo
   - Exportar a Excel con formato
   - Selección de secciones a incluir
```

### 5.5 Módulo 5: Exportación de Informes

**Responsabilidad**: Generar informes en PDF y Excel con formato profesional.

```python
class ReportExporter:
    def to_excel(self, stats_data, charts, filename) -> str:
        """Exporta informe completo a Excel con formato y gráficos"""

    def to_pdf(self, stats_data, charts, filename) -> str:
        """Exporta informe completo a PDF"""

    def to_html(self, stats_data, charts, filename) -> str:
        """Exporta informe como HTML interactivo"""
```

---

## 6. REPORTES A GENERAR (DETALLE)

### 6.1 Reporte: Delitos con Modalidades - Comparativo

| Columna                              | Descripción                    |
| ------------------------------------ | ------------------------------ |
| DELITO                               | Tipo de delito con modalidad   |
| Período 1 (ej: 21-27 Ene 2026)       | Cantidad en el primer período  |
| Período 2 (ej: 28 Ene - 03 Feb 2026) | Cantidad en el segundo período |
| Diferencia en cantidades             | Período 2 - Período 1          |
| Diferencia porcentual                | ((P2-P1)/P1) × 100             |
| **SUMA TOTAL**                       | Totales por columna            |

**Gráfico**: Barras agrupadas comparando ambos períodos por tipo de delito.

### 6.2 Reporte: Delitos por Día de la Semana

| Columna                     | Descripción           |
| --------------------------- | --------------------- |
| DELITO                      | Tipo de delito        |
| LUNES a DOMINGO             | Cantidad por cada día |
| TOTAL DELITO POR DELITO     | Suma horizontal       |
| **TOTAL DE HECHOS POR DÍA** | Suma vertical por día |

**Gráfico**: Barras agrupadas por tipo de delito y día de la semana.

### 6.3 Reporte: Franja Horaria

| Columna            | Descripción       |
| ------------------ | ----------------- |
| FRANJA HORARIA     | Categoría horaria |
| Cantidad (período) | Número de hechos  |
| Porcentaje         | % del total       |

**Franjas**: MADRUGADA (00:00-04:59), MAÑANA (05:00-08:59), VESPERTINA (09:00-12:59), SIESTA (13:00-16:59), TARDE (17:00-19:59), NOCHE (20:00-23:59)

**Gráfico**: Barras verticales con etiqueta de valor.

### 6.4 Reporte: Medios de Movilidad

| Columna            | Descripción      |
| ------------------ | ---------------- |
| MEDIO DE MOVILIDAD | Tipo             |
| Cantidad           | Número de hechos |
| Porcentaje         | % del total      |

**Gráfico**: Barras verticales.

### 6.5 Reporte: Armas Utilizadas (Solo Robos Agravados)

| Columna      | Descripción      |
| ------------ | ---------------- |
| TIPO DE ARMA | Categoría        |
| Cantidad     | Número de hechos |
| Porcentaje   | % del total      |

**Nota**: Este reporte filtra SOLO robos agravados.
**Gráfico**: Barras verticales.

### 6.6 Reporte: Ámbito de Ocurrencia

| Columna    | Descripción       |
| ---------- | ----------------- |
| ÁMBITO     | Lugar clasificado |
| Cantidad   | Número de hechos  |
| Porcentaje | % del total       |

**Gráfico**: Barras verticales.

### 6.7 Reporte: Meses de Ocurrencia

| Columna    | Descripción       |
| ---------- | ----------------- |
| MES        | Enero a Diciembre |
| Cantidad   | Número de hechos  |
| Porcentaje | % del total       |

**Gráfico**: Barras verticales.

### 6.8 Reporte: Jurisdicciones (Comisarías Capital)

| Columna      | Descripción                                     |
| ------------ | ----------------------------------------------- |
| JURISDICCIÓN | Comisaría 1ª a 15ª + Tafí Viejo + Villa Carmela |
| Cantidad     | Número de hechos                                |
| Porcentaje   | % del total                                     |

**Gráfico**: Barras verticales.

### 6.9 Reporte: Jurisdicciones (Todas las Comisarías por UR)

- Tabla extendida con TODAS las comisarías de URN, URC, URO, URE, URS
- Porcentajes por comisaría

**Gráfico**: Barras horizontales (por la cantidad de categorías).

### 6.10 Reporte: Delitos por Unidad Regional

| Columna         | Descripción                      |
| --------------- | -------------------------------- |
| UNIDAD REGIONAL | Capital, Norte, Oeste, Este, Sur |
| Cantidad        | Número de hechos                 |
| Porcentaje      | % del total                      |

**Gráfico**: Barras verticales.

### 6.11 Reporte: Delitos por Franja Horaria (Matriz Cruzada)

| Columna              | Descripción         |
| -------------------- | ------------------- |
| DELITO               | Tipo de delito      |
| MADRUGADA a NOCHE    | Cantidad por franja |
| TOTAL DELITO         | Suma horizontal     |
| **TOTAL POR FRANJA** | Suma vertical       |

**Gráfico**: Barras agrupadas por delito y franja.

---

## 7. DISEÑO VISUAL (ESTILO POWER BI)

### 7.1 Paleta de Colores para Tablas

```css
/* Encabezados */
header-bg: #CC0000 (rojo fuerte)
header-text: #FFFFFF (blanco)

/* Columna de período/fecha */
date-header-bg: #0000FF (azul)
date-header-text: #FFFFFF

/* Columna de porcentaje */
pct-header-bg: #FFDAB9 (durazno)

/* Filas de datos */
row-even-bg: #F5F5F5
row-odd-bg: #FFFFFF

/* Fila de totales */
total-bg: #FFFF00 (amarillo)
total-text: #CC0000 (rojo)

/* Valores positivos/negativos en comparativos */
positive-change: #00AA00 (verde) ↑
negative-change: #CC0000 (rojo) ↓
```

### 7.2 Estilo de Gráficos

- **Barras**: Color azul (#4472C4) principal, con etiquetas de valor sobre cada barra
- **Ejes**: Labels rotados 45° cuando hay muchas categorías
- **Título**: En rojo, centrado, fuente bold
- **Fondo**: Blanco limpio sin gridlines excesivas
- **Comparativos**: Barras lado a lado en azul y rojo

---

## 8. ESTRUCTURA DEL PROYECTO

```
mapa-delictual-app/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── __init__.py
│   ├── settings.py              # Configuración general
│   └── shapefile_registry.py    # Registro de rutas de shapefiles
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py            # ShapefileLoader
│   │   ├── normalizer.py        # Normalización de columnas
│   │   └── validator.py         # Validación de datos
│   ├── stats/
│   │   ├── __init__.py
│   │   ├── engine.py            # StatsEngine
│   │   ├── temporal.py          # Estadísticas temporales
│   │   ├── geographic.py        # Estadísticas geográficas
│   │   └── comparative.py       # Comparativo entre períodos
│   ├── charts/
│   │   ├── __init__.py
│   │   ├── generator.py         # ChartGenerator
│   │   ├── styles.py            # Estilos Power BI
│   │   └── templates.py         # Plantillas de gráficos
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── exporter.py          # ReportExporter
│   │   ├── pdf_builder.py       # Constructor de PDF
│   │   └── excel_builder.py     # Constructor de Excel
│   └── ui/
│       ├── __init__.py
│       ├── app.py               # App principal (Streamlit/Dash)
│       ├── pages/
│       │   ├── home.py          # Página de inicio
│       │   ├── delitos.py       # Página de delitos
│       │   ├── temporal.py      # Análisis temporal
│       │   ├── caracteristicas.py  # Movilidad/Armas/Ámbito
│       │   ├── geografico.py    # Análisis geográfico
│       │   └── comparativo.py   # Comparativo
│       └── components/
│           ├── filters.py       # Componentes de filtros
│           ├── kpi_cards.py     # Tarjetas KPI
│           └── tables.py        # Tablas estilizadas
├── tests/
│   ├── test_loader.py
│   ├── test_stats.py
│   └── test_charts.py
└── docs/
    ├── manual_usuario.md
    └── diccionario_datos.md
```

---

## 9. DEPENDENCIAS (requirements.txt)

```txt
# Core Data
geopandas>=0.14.0
pandas>=2.1.0
numpy>=1.25.0
fiona>=1.9.0
pyshp>=2.3.0
shapely>=2.0.0

# Visualización
plotly>=5.18.0
matplotlib>=3.8.0
seaborn>=0.13.0

# Dashboard UI (elegir uno)
streamlit>=1.29.0
# dash>=2.14.0  # Alternativa a Streamlit

# Mapas
folium>=0.15.0
streamlit-folium>=0.15.0

# Exportación
openpyxl>=3.1.0
xlsxwriter>=3.1.0
reportlab>=4.0.0
pdfkit>=1.0.0
Jinja2>=3.1.0

# Utilidades
python-dateutil>=2.8.0
tqdm>=4.66.0
loguru>=0.7.0
```

---

## 10. PLAN DE DESARROLLO - FASES Y CRONOGRAMA

### FASE 0: Exploración y Validación (1 semana)

| #   | Tarea                                             | Prioridad | Estimación |
| --- | ------------------------------------------------- | --------- | ---------- |
| 0.1 | Explorar estructura real de los shapefiles (.dbf) | CRÍTICA   | 2 días     |
| 0.2 | Documentar campos reales de cada tipo de shape    | CRÍTICA   | 1 día      |
| 0.3 | Identificar inconsistencias entre shapefiles      | ALTA      | 1 día      |
| 0.4 | Crear diccionario de mapeo de columnas            | ALTA      | 1 día      |

### FASE 1: Capa de Datos (2 semanas)

| #   | Tarea                                                 | Prioridad | Estimación |
| --- | ----------------------------------------------------- | --------- | ---------- |
| 1.1 | Implementar `ShapefileLoader` básico                  | CRÍTICA   | 2 días     |
| 1.2 | Crear registro de rutas de shapefiles                 | ALTA      | 1 día      |
| 1.3 | Implementar normalización de columnas                 | ALTA      | 2 días     |
| 1.4 | Derivar campos calculados (franja horaria, día, etc.) | ALTA      | 2 días     |
| 1.5 | Asignación automática de Unidad Regional              | MEDIA     | 1 día      |
| 1.6 | Validación y manejo de errores                        | MEDIA     | 1 día      |
| 1.7 | Tests unitarios del módulo de datos                   | MEDIA     | 1 día      |

### FASE 2: Motor de Estadísticas (2 semanas)

| #   | Tarea                                                      | Prioridad | Estimación |
| --- | ---------------------------------------------------------- | --------- | ---------- |
| 2.1 | Implementar filtro por rango de fechas                     | CRÍTICA   | 1 día      |
| 2.2 | Estadísticas de delitos por modalidad                      | CRÍTICA   | 1 día      |
| 2.3 | Estadísticas temporales (día, franja, mes)                 | CRÍTICA   | 2 días     |
| 2.4 | Estadísticas de características (movilidad, armas, ámbito) | ALTA      | 2 días     |
| 2.5 | Estadísticas geográficas (jurisdicción, UR)                | ALTA      | 1 día      |
| 2.6 | Motor comparativo entre períodos                           | ALTA      | 2 días     |
| 2.7 | Matrices cruzadas (delito x día, delito x franja)          | MEDIA     | 1 día      |
| 2.8 | Tests unitarios del motor                                  | MEDIA     | 1 día      |

### FASE 3: Gráficos y Visualización (2 semanas)

| #   | Tarea                                                | Prioridad | Estimación |
| --- | ---------------------------------------------------- | --------- | ---------- |
| 3.1 | Definir estilos Power BI (colores, fuentes, layouts) | ALTA      | 1 día      |
| 3.2 | Gráficos de barras básicos con etiquetas             | CRÍTICA   | 2 días     |
| 3.3 | Tablas estilizadas con formato condicional           | CRÍTICA   | 2 días     |
| 3.4 | Gráficos comparativos (barras agrupadas)             | ALTA      | 1 día      |
| 3.5 | Gráficos de barras apiladas/matrices                 | MEDIA     | 1 día      |
| 3.6 | Mapas interactivos con Folium                        | MEDIA     | 2 días     |
| 3.7 | KPI cards y mini-gráficos                            | BAJA      | 1 día      |

### FASE 4: Dashboard/UI (2 semanas)

| #   | Tarea                                      | Prioridad | Estimación |
| --- | ------------------------------------------ | --------- | ---------- |
| 4.1 | Estructura base de la aplicación Streamlit | CRÍTICA   | 1 día      |
| 4.2 | Página de inicio con resumen y KPIs        | ALTA      | 1 día      |
| 4.3 | Filtros globales (fecha, UR, comisaría)    | CRÍTICA   | 2 días     |
| 4.4 | Página de delitos por modalidad            | ALTA      | 1 día      |
| 4.5 | Página de análisis temporal                | ALTA      | 1 día      |
| 4.6 | Página de características del hecho        | ALTA      | 1 día      |
| 4.7 | Página de análisis geográfico              | ALTA      | 1 día      |
| 4.8 | Página comparativa                         | ALTA      | 1 día      |
| 4.9 | Navegación y sidebar                       | MEDIA     | 1 día      |

### FASE 5: Exportación (1 semana)

| #   | Tarea                                      | Prioridad | Estimación |
| --- | ------------------------------------------ | --------- | ---------- |
| 5.1 | Exportación a Excel con formato y gráficos | ALTA      | 2 días     |
| 5.2 | Exportación a PDF                          | ALTA      | 2 días     |
| 5.3 | Selector de secciones a exportar           | MEDIA     | 1 día      |

### FASE 6: Testing y Despliegue (1 semana)

| #   | Tarea                               | Prioridad | Estimación |
| --- | ----------------------------------- | --------- | ---------- |
| 6.1 | Testing integral con datos reales   | CRÍTICA   | 2 días     |
| 6.2 | Optimización de rendimiento (caché) | MEDIA     | 1 día      |
| 6.3 | Empaquetado como .exe (PyInstaller) | ALTA      | 1 día      |
| 6.4 | Manual de usuario                   | MEDIA     | 1 día      |

### Resumen del Cronograma

```
FASE 0: Exploración .............. Semana 1
FASE 1: Capa de Datos ........... Semanas 2-3
FASE 2: Motor Estadísticas ...... Semanas 4-5
FASE 3: Gráficos ................ Semanas 6-7
FASE 4: Dashboard/UI ............ Semanas 8-9
FASE 5: Exportación ............. Semana 10
FASE 6: Testing/Despliegue ...... Semana 11
─────────────────────────────────────────────
TOTAL ESTIMADO: ~11 semanas (~3 meses)
```

---

## 11. CONSIDERACIONES TÉCNICAS

### 11.1 Compatibilidad con QGIS 2.14.14 Essen

- Los shapefiles generados por QGIS 2.14 usan encoding **Latin1** o **CP1252** (verificar)
- Formato shapefile estándar: `.shp` + `.dbf` + `.shx` + `.prj` (mínimo)
- Verificar sistema de coordenadas (probablemente EPSG:4326 o EPSG:22174 - Posgar 94)
- Los campos en `.dbf` tienen límite de 10 caracteres en nombres (formato dBASE IV)

### 11.2 Rendimiento

- ~130 shapefiles a cargar; implementar caché con `pickle` o SQLite
- Para datos grandes: usar `dask-geopandas` o procesamiento lazy
- Pre-calcular estadísticas al cargar datos y cachear resultados

### 11.3 Manejo de Datos Especiales

- Valores `#NO_CONSTA`, `#NINGUNA`, `#OTRO`: tratar como categorías especiales
- División por cero en porcentajes: manejar `#¡DIV/0!` mostrando `0.00%` o `N/A`
- Fechas sin hora: asignar a categoría especial o excluir de análisis horario

### 11.4 Ruta de Red (Z:\)

- La unidad Z:\ es probablemente un mapeo de red
- Implementar verificación de conectividad antes de cargar
- Opción de copiar datos localmente para trabajo offline
- Timeout configurable para lectura de archivos remotos

---

## 12. PASO INMEDIATO SIGUIENTE - FASE 0

Para comenzar, se necesita **explorar la estructura real de los shapefiles**. Script de exploración:

```python
import geopandas as gpd
import os

# Ejemplo: explorar un shapefile
sample_path = r"Z:\MAPA DEL DELITO\MAPAS DEL DELITO POR JURISDICCIONES\CRIA6-URC-2020\MAPA DELICTUAL CRIA6-URC-2020\MAPA DELICTUAL CRIA6-URC-2020.shp"

gdf = gpd.read_file(sample_path, encoding='latin1')
print("=== COLUMNAS ===")
print(gdf.columns.tolist())
print("\n=== TIPOS DE DATOS ===")
print(gdf.dtypes)
print("\n=== PRIMERAS FILAS ===")
print(gdf.head())
print("\n=== VALORES ÚNICOS POR COLUMNA ===")
for col in gdf.columns:
    if col != 'geometry':
        print(f"\n{col}: {gdf[col].nunique()} valores únicos")
        print(gdf[col].unique()[:10])
print(f"\n=== TOTAL REGISTROS: {len(gdf)} ===")
print(f"=== CRS: {gdf.crs} ===")
```

---

## 13. RIESGOS Y MITIGACIONES

| Riesgo                                      | Probabilidad | Impacto | Mitigación                              |
| ------------------------------------------- | ------------ | ------- | --------------------------------------- |
| Shapefiles con esquemas diferentes          | ALTA         | ALTO    | Fase 0 de exploración + mapeo flexible  |
| Datos faltantes o inconsistentes            | ALTA         | MEDIO   | Validador robusto + valores por defecto |
| Unidad Z:\ no disponible                    | MEDIA        | ALTO    | Modo offline con copia local            |
| Encoding incorrecto (ñ, acentos)            | ALTA         | BAJO    | Detección automática de encoding        |
| Campos truncados en .dbf (10 chars)         | ALTA         | MEDIO   | Mapeo de nombres abreviados             |
| Rendimiento con muchos shapes               | MEDIA        | MEDIO   | Caché y carga lazy                      |
| Gráficos no coinciden con el formato actual | BAJA         | BAJO    | Plantillas configurables                |

---

## 14. ENTREGABLES

1. **Aplicación ejecutable** (.exe o lanzador .bat)
2. **Dashboard web** accesible por navegador (localhost)
3. **Generador de informes PDF** con formato idéntico al actual
4. **Generador de informes Excel** con gráficos embebidos
5. **Manual de usuario** con capturas de pantalla
6. **Código fuente** documentado en repositorio Git

---

## 15. PRÓXIMOS PASOS INMEDIATOS

1. ✅ **Plan creado** (este documento)
2. ⬜ **Explorar 3-5 shapefiles de muestra** para validar campos reales
3. ⬜ **Instalar dependencias** (`pip install geopandas plotly streamlit`)
4. ⬜ **Crear script de exploración** para documentar la estructura de datos
5. ⬜ **Iniciar Fase 1** con el `ShapefileLoader`

---

_Documento generado el 25/02/2026 - Plan v1.0_
