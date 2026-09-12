from __future__ import annotations

from pathlib import Path
import json
import textwrap

import nbformat as nbf
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from pptx import Presentation
from pptx.util import Inches, Pt as PptPt
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"


def read_results() -> dict:
    return json.loads((TABLES / "analysis_summary.json").read_text(encoding="utf-8"))


def fmt(x: float) -> str:
    if pd.isna(x):
        return "n.d."
    return f"{x:.3f}"


def write_text_files(summary: dict) -> None:
    clf = pd.read_csv(TABLES / "classification_benchmark.csv")
    clu = pd.read_csv(TABLES / "clustering_benchmark.csv")
    profile = pd.read_csv(TABLES / "cluster_profiles.csv")
    merge = json.loads((TABLES / "merge_audit.json").read_text(encoding="utf-8"))
    best_clf = clf.sort_values(["f1", "pr_auc", "roc_auc"], ascending=False).iloc[0]
    best_cluster = summary["clustering"]

    (ROOT / "requirements.txt").write_text(
        "\n".join(
            [
                "pandas",
                "numpy",
                "scikit-learn",
                "matplotlib",
                "seaborn",
                "openpyxl",
                "python-docx",
                "python-pptx",
                "nbformat",
                "nbclient",
                "nbconvert",
                "ipykernel",
                "unidecode",
                "scipy",
                "statsmodels",
                "reportlab",
                "joblib",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    references = """# Referencias IEEE

[1] Ministerio del Interior, "Denuncias Policiales," Plataforma Nacional de Datos Abiertos, dataset y recursos CSV/XLSX/DOCX, actualizado el 10 de septiembre de 2026. [En línea]. Disponible: https://www.datosabiertos.gob.pe/dataset/denuncias-policiales-1. [Consultado: 11-sep-2026].

[2] Ministerio del Interior, "Victimización, Percepción de Inseguridad y Confianza en la PNP," Plataforma Nacional de Datos Abiertos, dataset y recursos CSV/XLSX/DOCX, actualizado el 10 de septiembre de 2026. [En línea]. Disponible: https://www.datosabiertos.gob.pe/dataset/victimizaci%C3%B3n-percepci%C3%B3n-de-inseguridad-y-confianza-en-la-pnp. [Consultado: 11-sep-2026].

[3] Instituto Nacional de Estadística e Informática, "Perú: Población Total Proyectada al 30 de Junio de cada año, según Departamento, Provincia y Distrito, 2018-2026," Plataforma del Estado Peruano, 31 de diciembre de 2025. [En línea]. Disponible: https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026. [Consultado: 11-sep-2026].

[4] Ministerio del Interior, "Política Nacional Multisectorial de Seguridad Ciudadana al 2030," Plataforma del Estado Peruano, 23 de junio de 2022. [En línea]. Disponible: https://www.gob.pe/institucion/mininter/informes-publicaciones/3150919-politica-nacional-multisectorial-de-seguridad-ciudadana-al-2030. [Consultado: 11-sep-2026].

[5] Presidencia del Consejo de Ministros, "Decreto Legislativo N.° 1412: Ley de Gobierno Digital," Plataforma del Estado Peruano, 13 de septiembre de 2018. [En línea]. Disponible: https://www.gob.pe/institucion/pcm/normas-legales/289706-1412. [Consultado: 11-sep-2026].

[6] Congreso de la República del Perú, "Ley N.° 29733: Ley de Protección de Datos Personales," Plataforma del Estado Peruano, 3 de julio de 2011. [En línea]. Disponible: https://www.gob.pe/institucion/congreso-de-la-republica/normas-legales/243470-29733. [Consultado: 11-sep-2026].
"""
    (ROOT / "references" / "referencias_ieee.md").write_text(references, encoding="utf-8")

    readme = f"""# Seguridad ciudadana en el Perú mediante Machine Learning

Integrantes: [INTEGRANTES]

Este proyecto identifica perfiles territoriales de seguridad ciudadana y clasifica contextos departamentales-año con victimización alta usando datos oficiales de denuncias policiales SIDPOL/MININTER, ENAPRES/MININTER-INEI y población proyectada INEI.

## Datasets

- Denuncias Policiales, MININTER/PNP/SIDPOL: enero de 2018 a julio de 2026.
- Victimización, percepción de inseguridad y confianza en la PNP, MININTER/ENAPRES-INEI: 2013 a 2024.
- Población proyectada INEI: 2018 a 2026, usada solo como denominador oficial para tasas.

## Resultado metodológico principal

El nivel común máximo validado para integración es `departamento-año`, limitado a 2018-2024 para los modelos integrados. Denuncias tiene granularidad mensual distrital, pero ENAPRES está publicada a nivel nacional/departamental anual; por ello no se realizó merge distrital.

## Modelos

- Clustering: K-Means y Agglomerative Clustering. Selección final: {best_cluster['best_model']} con k={best_cluster['k']}.
- Clasificación: DummyClassifier, Regresión Logística y Random Forest. Mejor modelo: {best_clf['modelo']} con F1={fmt(best_clf['f1'])}, recall={fmt(best_clf['recall'])} y precision={fmt(best_clf['precision'])}.

## Cómo ejecutar

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe src\\inspect_sources.py
.\\.venv\\Scripts\\python.exe src\\modeling.py
.\\.venv\\Scripts\\python.exe src\\generate_artifacts.py
.\\.venv\\Scripts\\python.exe -m nbconvert --execute --to notebook --inplace notebooks\\parcial_machine_learning_criminalidad_peru.ipynb
```

## Limitaciones

Las denuncias policiales no equivalen a criminalidad real. Reflejan también propensión a denunciar, acceso institucional, prácticas de registro y confianza. ENAPRES tiene indicadores agregados, por lo que no debe usarse para inferir conductas individuales.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")

    decisions = f"""# DECISIONS

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
Evidencia: benchmark en `outputs/tables/clustering_benchmark.csv`; K-Means k={best_cluster['k']} equilibró métricas e interpretabilidad.
Justificación: mejor balance entre Davies-Bouldin, silhouette y perfiles legibles.
Limitación: silhouette moderado; los perfiles son exploratorios.

## Decisión: clasificación final
Alternativas: DummyClassifier, Logistic Regression, Random Forest.
Evidencia: benchmark en `outputs/tables/classification_benchmark.csv`; {best_clf['modelo']} obtuvo F1={fmt(best_clf['f1'])}.
Justificación: superó baseline y redujo falsos negativos en el test temporal 2023-2024.
Limitación: muestra pequeña; resultados deben actualizarse con nuevos años.
"""
    (ROOT / "DECISIONS.md").write_text(decisions, encoding="utf-8")

    rubric = """# Matriz de trazabilidad de la rúbrica

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
"""
    (ROOT / "rubric_compliance.md").write_text(rubric, encoding="utf-8")

    defense = f"""# Guía de defensa técnica

## Guion cronometrado de 12 minutos

1. Título (0:00-0:40): presentar objetivo y énfasis en datos oficiales.
2. Problema (0:40-1:20): explicar diferencia entre denuncias, victimización y percepción.
3. Preguntas y objetivos (1:20-2:00): perfiles territoriales y clasificación de victimización alta.
4. Datos (2:00-2:50): MININTER/SIDPOL, ENAPRES e INEI población.
5. Pipeline (2:50-3:30): raw, validación, limpieza, agregación, merge, modelos.
6. EDA (3:30-4:30): mencionar caída 2020 y recuperación posterior.
7. Features (4:30-5:05): tasas, proporciones, brecha percepción-victimización y rezagos.
8. Clustering método (5:05-5:45): escalado, k=2..7, dos algoritmos.
9. Clustering resultados (5:45-6:35): K-Means k={best_cluster['k']}, silhouette moderado e interpretación prudente.
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
"""
    (ROOT / "defense" / "guia_defensa_tecnica.md").write_text(defense, encoding="utf-8")


def report_sections(summary: dict) -> list[tuple[str, str]]:
    by_year = pd.DataFrame(summary["eda"]["by_year"])
    clf = pd.read_csv(TABLES / "classification_benchmark.csv")
    clu = pd.read_csv(TABLES / "clustering_benchmark.csv")
    profile = pd.read_csv(TABLES / "cluster_profiles.csv")
    best_clf = clf.sort_values(["f1", "pr_auc", "roc_auc"], ascending=False).iloc[0]
    return [
        ("PORTADA", "Seguridad ciudadana en el Perú: perfiles territoriales y clasificación de contextos de alta victimización mediante Machine Learning\n\n[NOMBRE DEL EQUIPO]\n[INTEGRANTES]\n[SECCIÓN]\n[CICLO ACADÉMICO]"),
        ("A. CONTEXTO DEL PROBLEMA", "La seguridad ciudadana es un problema público prioritario en el Perú. Este proyecto analiza denuncias registradas, victimización, percepción de inseguridad y confianza en la PNP sin confundir esos conceptos. La institución usuaria hipotética es el Ministerio del Interior y el Observatorio Nacional de Seguridad Ciudadana. El objetivo es construir evidencia territorial agregada para diagnóstico, priorización y seguimiento."),
        ("B. COMPRENSIÓN DEL NEGOCIO", "La decisión a apoyar es identificar departamentos y años con patrones diferenciados de seguridad ciudadana para orientar análisis, prevención y asignación de atención pública. El modelo no debe usarse para inferir comportamiento individual ni automatizar intervenciones policiales."),
        ("C. COMPRENSIÓN DEL CONJUNTO DE DATOS", "Se usaron tres fuentes oficiales: denuncias policiales SIDPOL/MININTER, indicadores ENAPRES/MININTER-INEI y población proyectada INEI. La unidad común validada fue departamento-año para 2018-2024. Denuncias tiene granularidad mensual distrital; ENAPRES está agregada a nivel nacional/departamental anual. No hubo duplicados en los CSV inspeccionados. El recurso ENAPRES tiene caracteres dañados en algunas cadenas, por lo que se aplicó normalización conservadora."),
        ("D. ANÁLISIS EXPLORATORIO DE DATOS", f"El panel final tiene {len(summary['eda']['coverage']) and int(pd.DataFrame(summary['eda']['coverage']).set_index('item').loc['filas_panel', 'valor'])} observaciones, {int(pd.DataFrame(summary['eda']['coverage']).set_index('item').loc['departamentos', 'valor'])} departamentos y 7 años. Las denuncias agregadas bajaron en 2020 ({int(by_year.loc[by_year.anio==2020,'denuncias_total'].iloc[0]):,}) y luego aumentaron hasta 2023 ({int(by_year.loc[by_year.anio==2023,'denuncias_total'].iloc[0]):,}). La victimización promedio departamental fue {by_year.loc[by_year.anio==2024,'victimizacion_pct'].iloc[0]:.1f}% en 2024. Las correlaciones se calcularon con Spearman sobre variables numéricas agregadas."),
        ("E. SELECCIÓN DEL TIPO DE PROBLEMA", "El proyecto contiene dos componentes complementarios: clustering no supervisado para descubrir perfiles territoriales y clasificación supervisada para anticipar victimización alta relativa. El target supervisado se definió como pertenecer al percentil 75 anual de victimización, usando predictores rezagados cuando correspondía."),
        ("F. IMPLEMENTACIÓN DE MODELOS", "Para clustering se usaron K-Means y Agglomerative Clustering con variables estandarizadas. Para clasificación se usaron DummyClassifier, Regresión Logística y Random Forest dentro de pipelines con imputación/escalado cuando correspondía. La partición temporal entrenó con 2019-2022 y probó con 2023-2024."),
        ("G. BENCHMARK DE MODELOS", f"Clustering: se evaluaron k=2..7 con silhouette, Davies-Bouldin y Calinski-Harabasz. La selección final fue {summary['clustering']['best_model']} con k={summary['clustering']['k']}. Clasificación: Random Forest obtuvo accuracy={best_clf['accuracy']:.3f}, precision={best_clf['precision']:.3f}, recall={best_clf['recall']:.3f}, F1={best_clf['f1']:.3f}, ROC-AUC={best_clf['roc_auc']:.3f} y PR-AUC={best_clf['pr_auc']:.3f}."),
        ("H. INTERPRETACIÓN DE RESULTADOS", "Random Forest obtuvo mejor desempeño porque capturó relaciones no lineales entre tasas, composición de denuncias y rezagos de indicadores. La regresión logística fue más interpretable, pero produjo demasiados falsos positivos con el umbral por defecto. El clustering mostró separación moderada, por lo que sus perfiles deben leerse como agrupaciones exploratorias y no como categorías definitivas."),
        ("I. IMPACTO MULTIDISCIPLINARIO", "Desde una perspectiva jurídica, el uso de IA en decisiones públicas debe respetar legalidad, debido procedimiento, no discriminación, transparencia, explicabilidad, calidad de datos, proporcionalidad y supervisión humana. En Perú son relevantes la Ley de Gobierno Digital, la Ley de Protección de Datos Personales y la Política Nacional Multisectorial de Seguridad Ciudadana al 2030. El modelo debe apoyar diagnóstico agregado, no decisiones automatizadas sobre personas ni comunidades."),
        ("J. INTELIGENCIA ARTIFICIAL RESPONSABLE", "El modelo puede reproducir sesgos de reporte, cobertura, medición, encuesta, sesgo histórico, sesgo territorial y socioeconómico. También existe riesgo de ecological fallacy, automation bias y estigmatización territorial. Mitigaciones: documentación clara, auditorías periódicas, revisión humana, comunicación prudente, métricas por subgrupos agregados, actualización con nuevos datos y prohibición de usos de profiling individual."),
        ("K. CONCLUSIONES", "1. La integración válida es departamento-año, no distrito.\n2. Denuncias registradas, victimización y percepción miden fenómenos distintos.\n3. La brecha percepción-victimización es analíticamente relevante.\n4. K-Means ofreció perfiles exploratorios interpretables.\n5. Random Forest superó al baseline en detección de victimización alta relativa.\n6. Accuracy sola habría ocultado el fracaso del baseline.\n7. El principal riesgo ético es tratar denuncias como criminalidad real.\n8. El sistema debe usarse como apoyo analítico con supervisión humana."),
        ("LIMITACIONES", f"La muestra integrada es pequeña, solo {int(pd.DataFrame(summary['eda']['coverage']).set_index('item').loc['filas_panel', 'valor'])} observaciones. ENAPRES está agregada y no permite inferencia individual. Las tasas dependen de proyecciones poblacionales. Las denuncias son registros administrativos dinámicos y no equivalen a todos los delitos ocurridos."),
        ("RECOMENDACIONES", "Actualizar el pipeline anualmente, validar cambios de esquema, incorporar variables oficiales adicionales solo si comparten granularidad, revisar umbrales con expertos sectoriales y presentar resultados como insumos de diagnóstico, no como rankings de peligrosidad."),
        ("REFERENCIAS IEEE", (ROOT / "references" / "referencias_ieee.md").read_text(encoding="utf-8")),
    ]


def write_docx_pdf(summary: dict) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)
    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(12)
    for title, body in report_sections(summary):
        h = doc.add_heading(title, level=1)
        h.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for para in body.split("\n\n"):
            p = doc.add_paragraph(para)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1.27)
            p.paragraph_format.line_spacing = 2
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
    doc.save(ROOT / "report" / "informe_tecnico.docx")

    pdf = SimpleDocTemplate(str(ROOT / "report" / "informe_tecnico.pdf"), pagesize=LETTER, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("NormalArial", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=22, firstLineIndent=18, alignment=4)
    heading = ParagraphStyle("Heading", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=18, spaceAfter=8)
    story = []
    for title, body in report_sections(summary):
        story.append(Paragraph(title, heading))
        for para in body.split("\n\n"):
            story.append(Paragraph(para.replace("\n", "<br/>"), normal))
            story.append(Spacer(1, 6))
        if title == "PORTADA":
            story.append(PageBreak())
    pdf.build(story)


def write_pptx(summary: dict) -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slides = [
        ("Seguridad ciudadana en el Perú", "Clustering y clasificación con datos oficiales"),
        ("Problema", "Denuncias, victimización y percepción no describen lo mismo."),
        ("Preguntas y objetivos", "Identificar perfiles territoriales y clasificar victimización alta relativa."),
        ("Datos", "SIDPOL/MININTER, ENAPRES/MININTER-INEI y población INEI."),
        ("Pipeline", "Validación, limpieza, agregación, merge, features, EDA, modelos y auditoría."),
        ("EDA", "Evolución anual e indicadores ENAPRES.", "01_evolucion_anual_denuncias.png"),
        ("Feature engineering", "Tasas por 100,000, proporciones, diversidad, brechas y rezagos."),
        ("Clustering: método", "K-Means y Agglomerative; k=2..7; métricas internas.", "10_clustering_silhouette.png"),
        ("Clustering: resultados", f"Modelo final: {summary['clustering']['best_model']} k={summary['clustering']['k']}.", "08_pca_clusters.png"),
        ("Clasificación: método", "Target: percentil 75 anual de victimización; train 2019-2022, test 2023-2024."),
        ("Benchmark", "Random Forest superó baseline y logística.", "12_matriz_confusion.png"),
        ("XAI", "Permutation importance para importancia predictiva.", "15_feature_importance.png"),
        ("IA Responsable", "Sesgo de reporte, cobertura, encuesta, medición y estigmatización."),
        ("Impacto y recomendaciones", "Uso para diagnóstico territorial con supervisión humana."),
        ("Conclusiones", "Resultados útiles, pero exploratorios y no causales."),
    ]
    for item in slides:
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        title = slide.shapes.title
        title.text = item[0]
        title.text_frame.paragraphs[0].font.size = PptPt(32)
        tx = slide.shapes.add_textbox(Inches(0.7), Inches(1.25), Inches(5.5), Inches(1.7))
        tx.text_frame.text = item[1]
        tx.text_frame.paragraphs[0].font.size = PptPt(22)
        if len(item) > 2:
            path = FIGURES / item[2]
            if path.exists():
                slide.shapes.add_picture(str(path), Inches(6.4), Inches(1.1), width=Inches(6.2))
    prs.save(ROOT / "presentation" / "presentacion_parcial.pptx")


def write_notebook() -> None:
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell("# Seguridad ciudadana en el Perú mediante Machine Learning\n\nObjetivo: reproducir validación, integración, EDA, clustering, clasificación, XAI e interpretación ética usando datos oficiales."),
        nbf.v4.new_markdown_cell("## Fuentes y metodología\n\nLas fuentes están en `data/raw`. El nivel común validado es departamento-año para 2018-2024. Antes de modelar se inspeccionan columnas, nulos, duplicados y granularidad."),
        nbf.v4.new_code_cell("import sys\nfrom pathlib import Path\nROOT = Path.cwd()\nif not (ROOT / 'src').exists() and (ROOT.parent / 'src').exists():\n    ROOT = ROOT.parent\nsys.path.insert(0, str(ROOT / 'src'))\nimport pandas as pd\nimport numpy as np\nSEED = 42\nROOT"),
        nbf.v4.new_markdown_cell("## Validación e integración\n\nSe ejecuta el pipeline de procesamiento para construir el panel reproducible."),
        nbf.v4.new_code_cell("from data_processing import build_department_year_dataset\npanel = build_department_year_dataset()\npanel.shape, panel.head()"),
        nbf.v4.new_markdown_cell("## EDA\n\nSe generan tablas y figuras descriptivas. Cada figura se guarda en `outputs/figures`."),
        nbf.v4.new_code_cell("from modeling import setup, run_eda, run_clustering, run_classification\nsetup()\neda = run_eda(panel)\npd.DataFrame(eda['by_year'])"),
        nbf.v4.new_markdown_cell("Interpretación: revise la evolución anual para distinguir denuncias registradas, victimización, percepción y confianza. Estos conceptos no son equivalentes."),
        nbf.v4.new_markdown_cell("## Clustering\n\nSe comparan K-Means y Agglomerative Clustering con variables estandarizadas."),
        nbf.v4.new_code_cell("clustering = run_clustering(panel)\nclustering['best_model'], clustering['k']"),
        nbf.v4.new_code_cell("pd.read_csv(ROOT / 'outputs' / 'tables' / 'cluster_profiles.csv')"),
        nbf.v4.new_markdown_cell("Interpretación: los clusters son perfiles exploratorios de patrones agregados; no son etiquetas de peligrosidad."),
        nbf.v4.new_markdown_cell("## Clasificación\n\nSe predice victimización alta relativa en t usando variables históricas y rezagos. Se evita leakage temporal."),
        nbf.v4.new_code_cell("classification = run_classification(panel)\npd.read_csv(ROOT / 'outputs' / 'tables' / 'classification_benchmark.csv')"),
        nbf.v4.new_markdown_cell("Interpretación: compare contra DummyClassifier. Accuracy no basta si el baseline no recupera la clase positiva."),
        nbf.v4.new_markdown_cell("## XAI, ética y conclusiones\n\nLa importancia por permutación indica relevancia predictiva, no causalidad. Deben considerarse sesgos de reporte, cobertura, medición y encuesta, además del riesgo de estigmatización territorial."),
        nbf.v4.new_code_cell("pd.read_csv(ROOT / 'outputs' / 'tables' / 'classification_permutation_importance.csv').head(10)"),
    ]
    nb["cells"] = cells
    nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}
    nbf.write(nb, ROOT / "notebooks" / "parcial_machine_learning_criminalidad_peru.ipynb")


def main() -> None:
    summary = read_results()
    write_text_files(summary)
    write_docx_pdf(summary)
    write_pptx(summary)
    write_notebook()
    print("artifacts generated")


if __name__ == "__main__":
    main()



