# DECISIONS

## Decisión: nivel de integración departamento-año
Alternativas: distrito-mes, distrito-año, provincia-año, departamento-año.
Evidencia: denuncias tiene distrito-mes-modalidad; ENAPRES tiene ámbito nacional/departamental anual; población INEI permite departamento-año.
Justificación: evita duplicación artificial y respeta la granularidad común.
Limitación: se pierde variación intradepartamental y mensual.

## Decisión: target de clasificación
Alternativas: mediana anual, percentil 75 anual, umbral institucional.
Evidencia: no se identificó umbral institucional en los datos descargados; el percentil 75 anual define "alto" relativo preservando comparabilidad temporal.
Justificación: target transparente para priorización analítica, no sancionadora.
Limitación: umbral relativo; no significa riesgo absoluto alto.

## Decisión: clustering final
Alternativas: K-Means k=2..7, Agglomerative Ward k=2..7.
Evidencia: benchmark en `outputs/tables/clustering_benchmark.csv`; K-Means k=2 equilibró métricas e interpretabilidad.
Justificación: mejor balance entre Davies-Bouldin, silhouette y perfiles legibles.
Limitación: silhouette moderado; los perfiles son exploratorios.

## Decisión: clasificación final
Alternativas: DummyClassifier, Logistic Regression, Random Forest.
Evidencia: benchmark en `outputs/tables/classification_benchmark.csv`; RandomForest obtuvo F1=0.875.
Justificación: superó baseline y redujo falsos negativos en el test temporal 2023-2024.
Limitación: muestra pequeña; resultados deben actualizarse con nuevos años.
