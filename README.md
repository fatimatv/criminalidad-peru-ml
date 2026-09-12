# Seguridad ciudadana en el Perú mediante Machine Learning

Integrantes: [INTEGRANTES]

Este proyecto identifica perfiles territoriales de seguridad ciudadana y clasifica contextos departamentales-año con victimización alta usando datos oficiales de denuncias policiales SIDPOL/MININTER, ENAPRES/MININTER-INEI y población proyectada INEI.

## Datasets

- Denuncias Policiales, MININTER/PNP/SIDPOL: enero de 2018 a julio de 2026.
- Victimización, percepción de inseguridad y confianza en la PNP, MININTER/ENAPRES-INEI: 2013 a 2024.
- Población proyectada INEI: 2018 a 2026, usada solo como denominador oficial para tasas.

## Resultado metodológico principal

El nivel común máximo validado para integración es `departamento-año`, limitado a 2018-2024 para los modelos integrados. Denuncias tiene granularidad mensual distrital, pero ENAPRES está publicada a nivel nacional/departamental anual; por ello no se realizó merge distrital.

## Modelos

- Clustering: K-Means y Agglomerative Clustering. Selección final: KMeans con k=2.
- Clasificación: DummyClassifier, Regresión Logística y Random Forest. Mejor modelo: RandomForest con F1=0.875, recall=1.000 y precision=0.778.

## Cómo ejecutar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\inspect_sources.py
.\.venv\Scripts\python.exe src\modeling.py
.\.venv\Scripts\python.exe src\generate_artifacts.py
.\.venv\Scripts\python.exe -m nbconvert --execute --to notebook --inplace notebooks\parcial_machine_learning_criminalidad_peru.ipynb
```

## Limitaciones

Las denuncias policiales no equivalen a criminalidad real. Reflejan también propensión a denunciar, acceso institucional, prácticas de registro y confianza. ENAPRES tiene indicadores agregados, por lo que no debe usarse para inferir conductas individuales.
