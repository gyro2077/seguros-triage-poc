# Spec 001: Motor de Triage de Siniestros (Clef-Flash Local vs Gemini 2.5 Flash Cloud)

Estado: aprobada

## Contexto y Objetivo

En el sector asegurador ecuatoriano (bajo normativa de la Superintendencia de Compañías, Valores y Seguros), los reclamos recibidos por canales no estructurados deben clasificarse inmediatamente en la taxonomía regulatoria (Generales vs Personas) para generar incidentes tipados en Jira Service Management.
Esta prueba de concepto compara un modelo de decisión directa System 1 en hardware local (Cloudflare/clef-flash cuantizado a 4-bit en GPU RTX 4060) contra un modelo generativo LLM en la nube (Google Gemini 2.5 Flash), midiendo latencia, determinismo de esquema y costo computacional.

## Usuarios y Actores

- **Analista de Operaciones / Triador**: Visualiza la evaluación comparativa, inspecciona los tickets mapeados y valida discrepancias.
- **Jira Service Management API**: Consumidor final del payload estructurado.

## Historias de Usuario

- **HU-1**: Como analista de operaciones, quiero pegar la notificación no estructurada de un siniestro para obtener en milisegundos la clasificación de macro-ramo, ramo específico, afectación a terceros y severidad operativa.
- **HU-2**: Como arquitecto de TI, quiero visualizar en tiempo real la comparativa de latencia (ms), consumo de tokens y proyección de costos de procesamiento de 100,000 incidentes mensuales.

## Taxonomía de Dominio (Catálogo Cerrado)

- **Macro-Ramo**: `['GENERALES', 'VIDA_Y_PERSONAS', 'MIXTO']`
- **Ramos Generales**: `['VEHICULOS', 'TODO_RIESGO_CONTRATISTA_MONTAJE', 'INCENDIO_LINEAS_ALIADAS', 'TRANSPORTE_CARGA', 'RESPONSABILIDAD_CIVIL', 'FIANZAS_GARANTIAS', 'ROTURA_MAQUINARIA']`
- **Ramos Vida y Personas**: `['ASISTENCIA_MEDICA_SALUD', 'ACCIDENTES_PERSONALES', 'VIDA_INDIVIDUAL_O_COLECTIVO', 'EXEQUIAS_SEPELIO']`
- **Severidad / SLA Jira**:
  - `1 (P1 - Crítico)`: Pérdida de vidas humanas, lesiones corporales de urgencia o paralización total de obras/operación. SLA < 2 horas.
  - `2 (P2 - Alto)`: Daño patrimonial severo sin riesgo vital, hospitalización programada. SLA < 6 horas.
  - `3 (P3 - Medio)`: Colisión vehicular leve, pérdida material menor cubierta con deducible estándar. SLA < 24 horas.
  - `4 (P4 - Bajo)`: Trámite documental, reembolso ambulatorio simple o consulta de indemnización. SLA < 48 horas.

## Requisitos Funcionales (Notación EARS)

- **RF-1**: CUANDO el usuario pulse el botón "Ejecutar Triage", EL SISTEMA enviará la carga útil en paralelo al endpoint de inferencia local de Clef-Flash y a la API de Gemini 2.5 Flash.
- **RF-2**: CUANDO Clef-Flash complete la evaluación por forward pass único, EL SISTEMA retornará el payload tipado con Macro-Ramo, Ramo Específico, indicio de lesiones corporales (bool), afectación de terceros (bool), Severidad (1-4) y la latencia exacta del cómputo en milisegundos.
- **RF-3**: CUANDO Gemini 2.5 Flash responda, EL SISTEMA extraerá el JSON tipado, registrará el tiempo transcurrido en red + inferencia, y calculará los tokens de entrada y salida consumidos.
- **RF-4**: SI la respuesta generativa de Gemini presenta un JSON malformado o un enum inexistente en el catálogo, ENTONCES EL SISTEMA marcará el resultado como "Fallo de Esquema" sin interrumpir la ejecución de Clef-Flash.
- **RF-5**: SI la clasificación detecta un siniestro `MIXTO` o severidad `1`, ENTONCES EL SISTEMA generará dos esquemas de ticket para Jira enlazados (Sub-ticket de Bienes Patrimoniales + Sub-ticket de Asistencia Médica / Personas).
- **RF-6**: EL SISTEMA calculará el costo acumulado proyectado a 100,000 incidentes/mes utilizando la tarifa oficial de tokens de Gemini frente al costo marginal de inferencia local ($0 por token).

## Requisitos No Funcionales

- **RNF-1**: El consumo de memoria VRAM de `clef-flash` en la GPU local RTX 4060 de 8GB no debe exceder 6.2 GB en estado de carga activa.
- **RNF-2**: La latencia de clasificación de Clef-Flash debe ser inferior a 150 ms por incidente.
- **RNF-3**: La interfaz debe ser desarrollada en React con diseño responsivo y sin el uso de recargas de página completas.

## Casos Límite

- Texto vacío o menor a 15 caracteres (debe rechazar la petición con error 422).
- Siniestro ambiguo sin mención explícita de montos o lesiones (el modelo debe clasificar con el score de menor severidad y marcar flag de revisión pericial).

## Criterios de Finalización

- Tests de endpoints FastAPI pasando en verde (`pytest`).
- Dashboard en React mostrando métricas sincronizadas y tickets generados.
