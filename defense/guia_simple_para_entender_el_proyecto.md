# Guia simple para entender el proyecto

## 1. La idea en una frase

El proyecto usa datos oficiales del Peru para comparar departamentos y encontrar patrones de seguridad ciudadana mediante Machine Learning.

No intenta decir que un lugar es "mas criminal". Lo correcto es decir que un departamento tiene mayor o menor nivel de denuncias registradas, victimización reportada, percepción de inseguridad o confianza en la PNP.

## 2. Que problema estudiamos

La seguridad ciudadana no se entiende con una sola cifra.

Por ejemplo, un departamento puede tener muchas denuncias registradas, pero eso no significa automaticamente que tenga mas delitos reales. Tambien puede significar que la gente denuncia mas, que hay mejor acceso a comisarias o que el registro policial es mas completo.

Tambien puede ocurrir que la percepcion de inseguridad sea alta aunque la victimización no sea tan alta. Por eso el proyecto mira varias dimensiones al mismo tiempo.

## 3. Que datos usamos

Usamos tres fuentes oficiales:

| Fuente | Que aporta | Para que sirve |
| --- | --- | --- |
| Denuncias policiales MININTER PNP SIDPOL | Registros de denuncias por lugar y fecha | Medir criminalidad registrada |
| ENAPRES MININTER INEI | Victimización, percepción de inseguridad y confianza en la PNP | Medir experiencia y percepcion ciudadana |
| Poblacion INEI | Poblacion por departamento y año | Calcular tasas comparables |

La unidad final del analisis es departamento año. Eso significa que cada fila representa un departamento en un año, por ejemplo Lima 2024 o Arequipa 2022.

## 4. Por que usamos departamento año

Porque las fuentes no tienen el mismo nivel de detalle.

Las denuncias tienen mucho detalle territorial, pero ENAPRES esta disponible de forma agregada. Para unirlas sin inventar informacion, el nivel comun valido fue departamento año.

El proyecto final tiene:

- 25 departamentos.
- 7 años, de 2018 a 2024.
- 175 observaciones departamento año.
- 0 duplicados en la base integrada.

## 5. Que paso con Lima y Callao

Al inicio, Lima no aparecia bien en la data modelada porque las fuentes usaban nombres distintos:

- Lima Metropolitana.
- Region Lima.
- Provincia Constitucional del Callao.

Para que el mapa, la poblacion y los modelos hablaran el mismo idioma, se normalizaron asi:

- Lima Metropolitana y Region Lima se integraron como LIMA.
- Provincia Constitucional del Callao se integro como CALLAO.

Esto no inventa datos. Solo corrige los nombres para trabajar al mismo nivel territorial.

## 6. Que es el pipeline

El pipeline es la ruta ordenada que siguio el proyecto:

1. Revisar las bases originales.
2. Limpiar nombres, fechas y categorias.
3. Agrupar la informacion por departamento y año.
4. Unir las fuentes.
5. Crear variables utiles.
6. Explorar los datos con graficos.
7. Entrenar modelos de clustering.
8. Entrenar modelos de clasificacion.
9. Evaluar resultados.
10. Explicar limitaciones y uso responsable.

En palabras simples: primero se ordenan los datos, despues se analizan y recien al final se modelan.

## 7. Variables importantes

Estas son las variables que debes entender:

| Variable | Significado simple |
| --- | --- |
| Denuncias registradas | Casos registrados por la policia |
| Tasa de denuncias por 100 mil habitantes | Denuncias ajustadas por poblacion para comparar departamentos |
| Victimización | Personas que reportan haber sido victimas |
| Percepcion de inseguridad | Personas que sienten inseguridad |
| Confianza en la PNP | Personas que declaran confianza en la policia |
| Brecha percepcion victimización | Diferencia entre sentir inseguridad y haber reportado victimización |

La tasa por 100 mil habitantes es importante porque no seria justo comparar Lima con un departamento pequeño usando solo cantidades totales.

## 8. Que es clustering

Clustering significa agrupar observaciones parecidas.

En este proyecto, el clustering busca responder:

Que departamentos años se parecen entre si segun denuncias registradas, victimización, percepcion de inseguridad y confianza en la PNP.

El modelo final fue K Means con 2 clusters.

## 9. Como interpretar los clusters

El resultado final separa dos perfiles:

| Cluster | Lectura simple |
| --- | --- |
| Cluster 0 | Menor presion registrada y percibida en promedio |
| Cluster 1 | Mayor tasa registrada y mayor percepcion de inseguridad en promedio |

No debes decir:

"El cluster 1 es el grupo criminal".

Debes decir:

"El cluster 1 agrupa observaciones con mayor presion registrada o percibida segun los indicadores disponibles".

## 10. Por que K Means y por que 2 clusters

Se compararon varios modelos y valores de k. K Means con k igual a 2 tuvo buen desempeño y era interpretable.

La interpretabilidad importa porque en un parcial no basta con mostrar metricas. Tambien hay que poder explicar que significa cada grupo.

La metrica silhouette del modelo final fue aproximadamente 0.242. No es perfecta, pero permite una separacion util para analizar perfiles agregados.

## 11. Que es clasificacion

Clasificacion significa entrenar un modelo para predecir una categoria.

En este proyecto, la categoria a predecir fue:

Si un departamento año tiene victimización alta.

Se considero victimización alta cuando la victimización del departamento año estaba en el percentil 75 o mas de su año.

## 12. Que modelos de clasificacion se compararon

Se compararon tres modelos:

| Modelo | Para que sirve en el proyecto |
| --- | --- |
| DummyClassifier | Es el modelo base. Sirve para saber si los otros modelos realmente mejoran algo |
| Regresion Logistica | Modelo interpretable y clasico |
| Random Forest | Modelo mas flexible que captura relaciones no lineales |

El mejor fue Random Forest.

## 13. Resultados principales del Random Forest

El Random Forest obtuvo:

- Accuracy: 0.92.
- Precision: 0.778.
- Recall: 1.00.
- F1: 0.875.
- ROC AUC: 0.974.
- PR AUC: 0.933.

La forma simple de explicarlo:

El modelo tuvo buen rendimiento para identificar casos de victimización alta en el conjunto de prueba. El recall de 1.00 significa que no dejo sin detectar casos positivos en esa prueba.

Pero hay que aclarar que esto no significa que el modelo sea perfecto para siempre. Significa que funciono bien con los datos y la forma de evaluacion usada.

## 14. Por que accuracy no basta

Accuracy significa porcentaje total de aciertos.

El problema es que puede engañar cuando una clase es mas frecuente que otra.

Ejemplo simple:

Si casi todos los casos fueran "no alta victimización", un modelo podria decir siempre "no" y aun asi acertar bastante. Por eso tambien miramos precision, recall y F1.

En el proyecto, el DummyClassifier tuvo accuracy de 0.72, pero F1 de 0. Eso demuestra que la accuracy sola no era suficiente.

## 15. Que significa XAI

XAI significa inteligencia artificial explicable.

En este proyecto usamos importancia por permutacion. En simple, consiste en alterar una variable y ver cuanto empeora el modelo.

Si al mover una variable el modelo empeora mucho, esa variable era importante para predecir.

Ojo: importante para predecir no significa causa. Que una variable ayude al modelo no significa que cause victimización.

## 16. Como leer los graficos principales

### Grafico de evolucion anual

Sirve para ver como cambian denuncias, victimización, percepcion y confianza entre 2018 y 2024.

Idea clave: la percepcion de inseguridad suele ser mayor que la victimización reportada.

### Grafico de tasa de denuncias 2024

Sirve para comparar departamentos usando denuncias por 100 mil habitantes.

Idea clave: se usa tasa porque los departamentos tienen poblaciones distintas.

### Scatter de victimización y percepcion

Sirve para ver si ambas variables se mueven juntas.

Idea clave: se relacionan, pero no son lo mismo.

### PCA de clusters

Sirve para visualizar los grupos en dos dimensiones.

Idea clave: PCA solo ayuda a ver el resultado; el clustering se entreno con variables estandarizadas.

### Mapa del Peru

Sirve para que los clusters tengan lectura territorial.

Idea clave: el mapa no crea el modelo, solo muestra geograficamente a que cluster pertenece cada departamento en el año seleccionado.

### Matriz de confusion

Sirve para ver aciertos y errores del modelo de clasificacion.

Idea clave: muestra cuantos casos positivos y negativos fueron bien o mal clasificados.

### Importancia de variables

Sirve para explicar que variables influyen mas en la prediccion.

Idea clave: explica el modelo, no demuestra causas.

## 17. Que debes decir en la defensa

Puedes decir algo asi:

"Nuestro proyecto analiza seguridad ciudadana en el Peru usando datos oficiales. Integramos denuncias policiales, ENAPRES y poblacion INEI a nivel departamento año. Luego usamos clustering para encontrar perfiles territoriales y clasificacion para identificar contextos con victimización alta. Tuvimos cuidado de no confundir denuncias con criminalidad real, porque una denuncia tambien depende de la confianza, el acceso institucional y la decision de denunciar."

## 18. Que debes evitar decir

Evita estas frases:

- "Este departamento es mas criminal".
- "El modelo prueba la causa de la delincuencia".
- "La policia debe actuar automaticamente donde el modelo diga".
- "La data representa todos los delitos reales".

Mejor usa estas frases:

- "Mayor tasa de denuncias registradas".
- "Mayor victimización reportada".
- "Mayor percepcion de inseguridad".
- "Perfil territorial con mayor presion registrada o percibida".
- "Resultado descriptivo y predictivo, no causal".

## 19. Preguntas que te pueden hacer

### Por que no trabajaron a nivel distrito

Porque ENAPRES no estaba disponible con el mismo detalle distrital para la integracion. Para no inventar datos, usamos departamento año.

### Por que usaron poblacion

Porque necesitabamos calcular tasas. Sin poblacion, solo tendriamos cantidades totales y eso favorece a departamentos grandes.

### Por que denuncias no equivalen a criminalidad real

Porque no todos los delitos se denuncian. La denuncia depende de confianza, acceso a comisarias, decision de denunciar y registro institucional.

### Por que usaron clustering

Porque queriamos encontrar perfiles territoriales sin imponer una etiqueta previa.

### Por que usaron clasificacion

Porque tambien queriamos probar si los indicadores disponibles ayudan a identificar contextos con victimización alta.

### Por que Random Forest fue el mejor

Porque obtuvo el mejor equilibrio de metricas, especialmente F1, recall y ROC AUC, comparado con el baseline y la regresion logistica.

### Que significa recall de 1.00

Que en el conjunto de prueba el modelo detecto todos los casos positivos de victimización alta.

### Que significa F1

F1 resume precision y recall. Sirve cuando importa equilibrar falsos positivos y falsos negativos.

### Que limitacion principal tiene el proyecto

Que trabaja con datos agregados y con denuncias registradas, no con todos los delitos reales. Por eso las conclusiones deben ser cuidadosas.

## 20. Explicacion de 30 segundos

"El proyecto compara departamentos del Peru entre 2018 y 2024 usando datos oficiales de denuncias, victimización, percepcion de inseguridad, confianza en la PNP y poblacion. Primero validamos que el nivel correcto era departamento año. Luego usamos clustering para agrupar perfiles parecidos y clasificacion para identificar casos de victimización alta. El mejor clasificador fue Random Forest, pero siempre interpretamos los resultados con cuidado porque denuncias no significan criminalidad real."

## 21. Explicacion de 2 minutos

"La idea central del proyecto es que la seguridad ciudadana no se mide con una sola variable. Las denuncias policiales muestran criminalidad registrada, pero no necesariamente criminalidad real. Por eso se integraron con ENAPRES, que incluye victimización, percepcion de inseguridad y confianza en la PNP. Tambien usamos poblacion INEI para calcular tasas comparables.

Antes de modelar, validamos la estructura de las bases. El nivel comun correcto fue departamento año, porque las fuentes no compartian una desagregacion distrital confiable. Despues limpiamos nombres territoriales, corregimos Lima y Callao, hicimos el merge, generamos variables y ejecutamos modelos.

En clustering, el resultado final fue K Means con 2 grupos. Un grupo refleja menor presion registrada y percibida, y el otro mayor tasa registrada y mayor percepcion promedio. En clasificacion, comparamos un modelo base, regresion logistica y Random Forest. Random Forest fue el mejor, con F1 de 0.875 y recall de 1.00.

La conclusion responsable es que el proyecto ayuda a describir y priorizar analisis territorial, pero no prueba causalidad ni debe usarse para etiquetar personas o territorios."

## 22. Lo mas importante para recordar

Si te preguntan algo y te pones nerviosa, vuelve a estas cuatro ideas:

1. El proyecto usa datos oficiales.
2. El nivel correcto es departamento año.
3. Denuncias no equivalen a criminalidad real.
4. Los modelos ayudan a encontrar patrones, no a probar causas.

