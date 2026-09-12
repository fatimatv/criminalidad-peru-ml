# Guía de defensa técnica

## Guion cronometrado de 12 minutos

1. Título (0:00-0:40): presentar objetivo y énfasis en datos oficiales.
2. Problema (0:40-1:20): explicar diferencia entre denuncias, victimización y percepción.
3. Preguntas y objetivos (1:20-2:00): perfiles territoriales y clasificación de victimización alta.
4. Datos (2:00-2:50): MININTER/SIDPOL, ENAPRES e INEI población.
5. Pipeline (2:50-3:30): raw, validación, limpieza, agregación, merge, modelos.
6. EDA (3:30-4:30): mencionar caída 2020 y recuperación posterior.
7. Features (4:30-5:05): tasas, proporciones, brecha percepción-victimización y rezagos.
8. Clustering método (5:05-5:45): escalado, k=2..7, dos algoritmos.
9. Clustering resultados (5:45-6:35): K-Means k=2, silhouette moderado e interpretación prudente.
10. Clasificación método (6:35-7:25): target q75 anual, train 2019-2022, test 2023-2024.
11. Benchmark (7:25-8:15): Random Forest supera baseline; accuracy sola no basta.
12. XAI (8:15-8:55): importancia predictiva no causalidad.
13. IA Responsable (8:55-10:00): sesgo de reporte, cobertura, encuesta, estigmatización.
14. Impacto (10:00-11:00): uso para diagnóstico territorial, no policing individual.
15. Conclusiones (11:00-12:00): valor del pipeline, límites y próximos pasos.

## Preguntas probables y respuestas

1. ¿Qué unidad de análisis usaron? Departamento-año, porque es la granularidad común verificable.
2. ¿Por qué no distrito? ENAPRES no está publicada a nivel distrital en este recurso.
3. ¿Qué años se integraron? 2018-2024.
4. ¿Qué pasó con 2025-2026? Solo denuncias, no integrables con ENAPRES.
5. ¿Hay datos personales? Los recursos trabajados están agregados.
6. ¿Por qué K-Means? Es un baseline robusto e interpretable para perfiles con variables estandarizadas.
7. ¿Por qué escogieron ese número de clusters? Por balance de métricas e interpretabilidad.
8. ¿Por qué no DBSCAN? No era necesario: muestra pequeña y objetivo de perfiles comparables, no detección de densidades.
9. ¿Qué significa silhouette? Mide cohesión y separación; valores mayores indican clusters más definidos.
10. ¿Cómo sabemos que los clusters son estables? Se probaron semillas y k alternativos.
11. ¿Por qué Regresión Logística? Es interpretable y sirve como modelo lineal comparativo.
12. ¿Por qué Random Forest? Captura relaciones no lineales y fue mejor en F1.
13. ¿Qué target usaron? Victimización en el percentil 75 anual.
14. ¿Qué es leakage? Usar información futura o contemporánea indebida para predecir el target.
15. ¿Cómo evitaron leakage? Predictores rezagados t-1 y test temporal posterior.
16. ¿Por qué Accuracy no es suficiente? El baseline tuvo accuracy alta pero recall cero para clase alta.
17. ¿Qué pasa si el dataset está desbalanceado? Se usan métricas como F1, recall, PR-AUC y class_weight.
18. ¿Qué es overfitting? Ajustarse demasiado al entrenamiento y fallar en datos nuevos.
19. ¿Por qué escalar variables? Para que magnitudes distintas no dominen K-Means/logística.
20. ¿Qué error importa más? Falsos negativos, porque omiten territorios que requieren atención analítica.
21. ¿Por qué correlación no implica causalidad? No controla mecanismos ni variables omitidas.
22. ¿Qué pasa si duplicamos el dataset? Se distorsionan entrenamiento, métricas y representatividad.
23. ¿Cómo desplegarían el modelo? Como tablero analítico con actualización anual y revisión humana.
24. ¿Cómo actualizarían con datos nuevos? Reejecutando pipeline y validando cambios de esquema.
25. ¿Cuál es el principal sesgo? Sesgo de reporte: denuncias dependen de propensión y acceso a denunciar.
26. ¿Por qué denuncias no equivalen a criminalidad? Porque capturan registros policiales, no todos los delitos ocurridos.
