# Matriz de trazabilidad de la rúbrica

| Criterio | Ponderación | Cómo se cumplió | Archivo | Sección | Evidencia |
|---|---:|---|---|---|---|
| Datos oficiales | 100% | Se descargaron datasets MININTER/INEI y fuente INEI de población | data/raw | Fase 1 | CSV/XLSX/DOCX |
| Diccionarios revisados | 100% | Se perfilaron diccionarios y metadatos | outputs/tables | Fase 1 | fase1_diccionario_*.csv |
| Granularidad y merge | 100% | Se validó departamento-año y merge one-to-one | outputs/tables/merge_audit.csv | C | 182 filas |
| EDA | 100% | Estadísticas, evolución, distribución, correlaciones y gráficos | outputs/figures, outputs/tables | D | Figuras 01-07 |
| Clustering | 100% | K-Means y Agglomerative con métricas | outputs/tables/clustering_benchmark.csv | F-G | Silhouette, DB, CH |
| Clasificación | 100% | Dummy, Logística y Random Forest con split temporal | outputs/tables/classification_benchmark.csv | F-G | Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC |
| XAI | 100% | Permutation importance y coeficientes/logística documentables | outputs/tables/classification_permutation_importance.csv | H | Importancias |
| IA Responsable | 100% | Sesgos, privacidad, estigmatización y mitigaciones | report/informe_tecnico.docx | J | Sección J |
| Perspectiva jurídica | 100% | Legalidad, transparencia, proporcionalidad y supervisión humana | report/informe_tecnico.docx | I | Sección I |
| Entregables | 100% | README, notebook, informe, PDF, PPTX, defensa y referencias | raíz del proyecto | Final | Archivos generados |
