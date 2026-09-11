from __future__ import annotations

from pathlib import Path
import json
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    calinski_harabasz_score,
    classification_report,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    silhouette_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from data_processing import ROOT, build_department_year_dataset
except ModuleNotFoundError:
    from src.data_processing import ROOT, build_department_year_dataset


warnings.filterwarnings("ignore", category=UserWarning)

FIGURES = ROOT / "outputs" / "figures"
TABLES = ROOT / "outputs" / "tables"
MODELS = ROOT / "outputs" / "models"
PROCESSED = ROOT / "data" / "processed"


CLUSTER_FEATURES = [
    "denuncias_tasa_100k",
    "prop_hurto",
    "prop_robo",
    "prop_estafa",
    "prop_extorsion",
    "prop_violencia_contra_la_mujer_e_integrantes",
    "diversidad_modalidades",
    "victimizacion_pct",
    "percepcion_inseguridad_pct",
    "confianza_pnp_pct",
    "brecha_percepcion_victimizacion",
]

CLASSIFICATION_FEATURES = [
    "denuncias_tasa_100k_lag1",
    "denuncias_total_lag1",
    "denuncias_tasa_yoy",
    "prop_hurto",
    "prop_robo",
    "prop_estafa",
    "prop_extorsion",
    "prop_violencia_contra_la_mujer_e_integrantes",
    "diversidad_modalidades",
    "victimizacion_pct_lag1",
    "percepcion_inseguridad_pct_lag1",
    "confianza_pnp_pct_lag1",
    "victimizacion_robo_pct_lag1",
    "victimizacion_estafa_pct_lag1",
]


def setup() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=0.9)
    plt.rcParams["figure.dpi"] = 140


def savefig(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def run_eda(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    df[numeric_cols].describe().T.to_csv(TABLES / "eda_descriptive_statistics.csv")
    df.isna().sum().rename("nulls").to_csv(TABLES / "eda_nulls.csv")

    coverage = pd.DataFrame(
        [
            {"item": "filas_panel", "valor": len(df)},
            {"item": "departamentos", "valor": df["departamento"].nunique()},
            {"item": "anio_min", "valor": df["anio"].min()},
            {"item": "anio_max", "valor": df["anio"].max()},
            {"item": "duplicados_departamento_anio", "valor": df.duplicated(["departamento", "anio"]).sum()},
        ]
    )
    coverage.to_csv(TABLES / "eda_coverage.csv", index=False)

    by_year = df.groupby("anio", as_index=False).agg(
        denuncias_total=("denuncias_total", "sum"),
        denuncias_tasa_100k=("denuncias_tasa_100k", "mean"),
        victimizacion_pct=("victimizacion_pct", "mean"),
        percepcion_inseguridad_pct=("percepcion_inseguridad_pct", "mean"),
        confianza_pnp_pct=("confianza_pnp_pct", "mean"),
    )
    by_year.to_csv(TABLES / "eda_evolucion_anual.csv", index=False)

    plt.figure(figsize=(8, 4))
    sns.lineplot(data=by_year, x="anio", y="denuncias_total", marker="o")
    plt.title("Denuncias registradas agregadas por año")
    plt.xlabel("Año")
    plt.ylabel("Denuncias registradas")
    savefig(FIGURES / "01_evolucion_anual_denuncias.png")

    latest = df[df["anio"] == df["anio"].max()].sort_values("denuncias_tasa_100k", ascending=False)
    plt.figure(figsize=(8, 7))
    sns.barplot(data=latest, y="departamento", x="denuncias_tasa_100k", color="#3B6EA8")
    plt.title("Tasa de denuncias registradas por 100,000 hab. (2024)")
    plt.xlabel("Denuncias por 100,000 habitantes")
    plt.ylabel("")
    savefig(FIGURES / "02_tasa_denuncias_departamento_2024.png")

    modality_cols = [c for c in df.columns if c.startswith("prop_")]
    comp = df.groupby("anio")[modality_cols].mean().reset_index()
    comp_long = comp.melt("anio", var_name="modalidad", value_name="proporcion")
    plt.figure(figsize=(9, 5))
    sns.lineplot(data=comp_long, x="anio", y="proporcion", hue="modalidad", marker="o")
    plt.title("Composición media de modalidades de denuncias")
    plt.xlabel("Año")
    plt.ylabel("Proporción")
    plt.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1, 1))
    savefig(FIGURES / "03_composicion_modalidades.png")

    indicators = ["victimizacion_pct", "percepcion_inseguridad_pct", "confianza_pnp_pct"]
    plt.figure(figsize=(8, 4))
    ind_year = df.groupby("anio")[indicators].mean().reset_index().melt("anio")
    sns.lineplot(data=ind_year, x="anio", y="value", hue="variable", marker="o")
    plt.title("Indicadores ENAPRES promedio departamental")
    plt.xlabel("Año")
    plt.ylabel("Porcentaje")
    savefig(FIGURES / "04_indicadores_enapres_anual.png")

    plt.figure(figsize=(6, 5))
    sns.scatterplot(data=df, x="victimizacion_pct", y="percepcion_inseguridad_pct", hue="anio", palette="viridis")
    plt.title("Victimización vs percepción de inseguridad")
    plt.xlabel("Victimización (%)")
    plt.ylabel("Percepción de inseguridad (%)")
    savefig(FIGURES / "05_scatter_victimizacion_percepcion.png")

    plt.figure(figsize=(6, 5))
    sns.scatterplot(data=df, x="denuncias_tasa_100k", y="victimizacion_pct", hue="anio", palette="viridis")
    plt.title("Denuncias registradas vs victimización")
    plt.xlabel("Denuncias por 100,000 hab.")
    plt.ylabel("Victimización (%)")
    savefig(FIGURES / "06_scatter_denuncias_victimizacion.png")

    corr_cols = [
        "denuncias_tasa_100k",
        "victimizacion_pct",
        "percepcion_inseguridad_pct",
        "confianza_pnp_pct",
        "brecha_percepcion_victimizacion",
        "diversidad_modalidades",
    ]
    corr = df[corr_cols].corr(method="spearman")
    corr.to_csv(TABLES / "eda_spearman_correlations.csv")
    plt.figure(figsize=(7, 5))
    sns.heatmap(corr, annot=True, cmap="vlag", center=0, fmt=".2f")
    plt.title("Correlaciones Spearman entre indicadores")
    savefig(FIGURES / "07_correlaciones_spearman.png")

    return {"coverage": coverage.to_dict(orient="records"), "by_year": by_year.to_dict(orient="records")}


def run_clustering(df: pd.DataFrame) -> dict:
    cluster_df = df.dropna(subset=CLUSTER_FEATURES).copy()
    X = cluster_df[CLUSTER_FEATURES]
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    rows = []
    for k in range(2, 8):
        km = KMeans(n_clusters=k, random_state=42, n_init=50)
        labels = km.fit_predict(Xs)
        rows.append(
            {
                "modelo": "KMeans",
                "k": k,
                "silhouette": silhouette_score(Xs, labels),
                "davies_bouldin": davies_bouldin_score(Xs, labels),
                "calinski_harabasz": calinski_harabasz_score(Xs, labels),
                "inertia": km.inertia_,
            }
        )
        agg = AgglomerativeClustering(n_clusters=k, linkage="ward")
        labels = agg.fit_predict(Xs)
        rows.append(
            {
                "modelo": "Agglomerative-Ward",
                "k": k,
                "silhouette": silhouette_score(Xs, labels),
                "davies_bouldin": davies_bouldin_score(Xs, labels),
                "calinski_harabasz": calinski_harabasz_score(Xs, labels),
                "inertia": np.nan,
            }
        )
    metrics = pd.DataFrame(rows)
    metrics.to_csv(TABLES / "clustering_benchmark.csv", index=False)

    candidates = metrics.copy()
    candidates["rank"] = (
        candidates["silhouette"].rank(ascending=False)
        + candidates["davies_bouldin"].rank(ascending=True)
        + candidates["calinski_harabasz"].rank(ascending=False)
    )
    best = candidates.sort_values(["rank", "k"]).iloc[0]
    final_k = int(best["k"])
    final_model_name = str(best["modelo"])
    if final_model_name == "KMeans":
        final_model = KMeans(n_clusters=final_k, random_state=42, n_init=50)
        labels = final_model.fit_predict(Xs)
    else:
        final_model = AgglomerativeClustering(n_clusters=final_k, linkage="ward")
        labels = final_model.fit_predict(Xs)
    cluster_df["cluster"] = labels

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(Xs)
    cluster_df["pca1"] = coords[:, 0]
    cluster_df["pca2"] = coords[:, 1]
    cluster_df.to_csv(PROCESSED / "panel_con_clusters.csv", index=False)

    profile = cluster_df.groupby("cluster").agg(
        observaciones=("cluster", "size"),
        territorios=("departamento", lambda s: ", ".join(sorted(s.unique())[:8])),
        denuncias_tasa_100k=("denuncias_tasa_100k", "mean"),
        victimization=("victimizacion_pct", "mean"),
        percepcion=("percepcion_inseguridad_pct", "mean"),
        confianza=("confianza_pnp_pct", "mean"),
        brecha=("brecha_percepcion_victimizacion", "mean"),
    ).reset_index()
    profile.to_csv(TABLES / "cluster_profiles.csv", index=False)

    plt.figure(figsize=(6, 5))
    sns.scatterplot(data=cluster_df, x="pca1", y="pca2", hue="cluster", palette="tab10", s=55)
    plt.title(f"Visualización PCA de clusters ({final_model_name}, k={final_k})")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    savefig(FIGURES / "08_pca_clusters.png")

    plt.figure(figsize=(8, 4))
    sns.lineplot(data=metrics[metrics["modelo"] == "KMeans"], x="k", y="inertia", marker="o")
    plt.title("K-Means: método del codo")
    plt.xlabel("k")
    plt.ylabel("Inercia")
    savefig(FIGURES / "09_kmeans_elbow.png")

    plt.figure(figsize=(8, 4))
    sns.lineplot(data=metrics, x="k", y="silhouette", hue="modelo", marker="o")
    plt.title("Comparación de silhouette por algoritmo")
    plt.xlabel("k")
    plt.ylabel("Silhouette")
    savefig(FIGURES / "10_clustering_silhouette.png")

    plt.figure(figsize=(10, 4))
    dendrogram(linkage(Xs, method="ward"), no_labels=True, color_threshold=None)
    plt.title("Dendrograma Ward (muestra completa departamento-año)")
    plt.xlabel("Observaciones")
    plt.ylabel("Distancia")
    savefig(FIGURES / "11_dendrograma_ward.png")

    stability_rows = []
    for seed in [1, 7, 21, 42, 99]:
        km = KMeans(n_clusters=final_k, random_state=seed, n_init=50)
        lab = km.fit_predict(Xs)
        stability_rows.append({"seed": seed, "silhouette": silhouette_score(Xs, lab), "davies_bouldin": davies_bouldin_score(Xs, lab)})
    stability = pd.DataFrame(stability_rows)
    stability.to_csv(TABLES / "clustering_stability_seeds.csv", index=False)

    joblib.dump({"scaler": scaler, "pca": pca, "model_name": final_model_name, "k": final_k}, MODELS / "clustering_artifacts.joblib")
    return {"best_model": final_model_name, "k": final_k, "metrics": metrics.to_dict(orient="records")}


def evaluate_classifier(name: str, model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        score = model.predict_proba(X_test)[:, 1]
    else:
        score = pred
    result = {
        "modelo": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, score) if len(set(y_test)) > 1 else np.nan,
        "pr_auc": average_precision_score(y_test, score) if len(set(y_test)) > 1 else np.nan,
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "classification_report": classification_report(y_test, pred, zero_division=0, output_dict=True),
    }
    return result


def run_classification(df: pd.DataFrame) -> dict:
    model_df = df[df["anio"] >= 2019].dropna(subset=CLASSIFICATION_FEATURES + ["victimizacion_alta_q75_anual"]).copy()
    X = model_df[CLASSIFICATION_FEATURES]
    y = model_df["victimizacion_alta_q75_anual"].astype(int)
    train_mask = model_df["anio"] <= 2022
    test_mask = model_df["anio"] >= 2023
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    preprocess = ColumnTransformer(
        transformers=[("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), CLASSIFICATION_FEATURES)],
        remainder="drop",
    )
    unscaled = ColumnTransformer(
        transformers=[("num", SimpleImputer(strategy="median"), CLASSIFICATION_FEATURES)],
        remainder="drop",
    )

    cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
    models = {
        "DummyClassifier": Pipeline([("prep", unscaled), ("clf", DummyClassifier(strategy="most_frequent"))]),
        "LogisticRegression": GridSearchCV(
            Pipeline([("prep", preprocess), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42, solver="liblinear"))]),
            {"clf__C": [0.1, 0.5, 1, 2]},
            scoring="f1",
            cv=cv,
        ),
        "RandomForest": GridSearchCV(
            Pipeline([("prep", unscaled), ("clf", RandomForestClassifier(random_state=42, class_weight="balanced"))]),
            {
                "clf__n_estimators": [100, 200],
                "clf__max_depth": [3, None],
                "clf__min_samples_leaf": [2, 4],
            },
            scoring="f1",
            cv=cv,
        ),
    }

    results = []
    fitted = {}
    for name, estimator in models.items():
        estimator.fit(X_train, y_train)
        final_estimator = estimator.best_estimator_ if isinstance(estimator, GridSearchCV) else estimator
        fitted[name] = final_estimator
        res = evaluate_classifier(name, final_estimator, X_test, y_test)
        res["cv_best_score"] = float(estimator.best_score_) if isinstance(estimator, GridSearchCV) else np.nan
        res["best_params"] = estimator.best_params_ if isinstance(estimator, GridSearchCV) else {}
        results.append(res)

    metrics = pd.DataFrame([{k: v for k, v in r.items() if k not in ["confusion_matrix", "classification_report", "best_params"]} for r in results])
    metrics.to_csv(TABLES / "classification_benchmark.csv", index=False)
    (TABLES / "classification_details.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    best_name = metrics.sort_values(["f1", "pr_auc", "roc_auc"], ascending=False).iloc[0]["modelo"]
    best_model = fitted[best_name]
    joblib.dump(best_model, MODELS / "best_classifier.joblib")

    pred = best_model.predict(X_test)
    cm = confusion_matrix(y_test, pred)
    plt.figure(figsize=(4, 3.5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title(f"Matriz de confusión: {best_name}")
    plt.xlabel("Predicho")
    plt.ylabel("Real")
    savefig(FIGURES / "12_matriz_confusion.png")

    if hasattr(best_model, "predict_proba") and len(set(y_test)) > 1:
        scores = best_model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, scores)
        precision, recall, _ = precision_recall_curve(y_test, scores)
        plt.figure(figsize=(5, 4))
        plt.plot(fpr, tpr)
        plt.plot([0, 1], [0, 1], linestyle="--", color="grey")
        plt.title(f"ROC: {best_name}")
        plt.xlabel("FPR")
        plt.ylabel("TPR")
        savefig(FIGURES / "13_roc_curve.png")
        plt.figure(figsize=(5, 4))
        plt.plot(recall, precision)
        plt.title(f"Precision-Recall: {best_name}")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        savefig(FIGURES / "14_precision_recall_curve.png")

    importance = permutation_importance(best_model, X_test, y_test, n_repeats=8, random_state=42, scoring="f1")
    imp = pd.DataFrame({"feature": CLASSIFICATION_FEATURES, "importance_mean": importance.importances_mean, "importance_std": importance.importances_std})
    imp.sort_values("importance_mean", ascending=False).to_csv(TABLES / "classification_permutation_importance.csv", index=False)
    plt.figure(figsize=(8, 5))
    sns.barplot(data=imp.sort_values("importance_mean", ascending=False).head(10), y="feature", x="importance_mean", color="#C5853E")
    plt.title("Importancia por permutación (F1)")
    plt.xlabel("Reducción media en F1")
    plt.ylabel("")
    savefig(FIGURES / "15_feature_importance.png")

    target_dist = model_df.groupby("anio")["victimizacion_alta_q75_anual"].value_counts().unstack(fill_value=0)
    target_dist.to_csv(TABLES / "classification_target_distribution.csv")

    threshold_rows = []
    if hasattr(best_model, "predict_proba"):
        scores = best_model.predict_proba(X_test)[:, 1]
        for threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:
            p = (scores >= threshold).astype(int)
            threshold_rows.append(
                {
                    "threshold": threshold,
                    "precision": precision_score(y_test, p, zero_division=0),
                    "recall": recall_score(y_test, p, zero_division=0),
                    "f1": f1_score(y_test, p, zero_division=0),
                }
            )
    pd.DataFrame(threshold_rows).to_csv(TABLES / "classification_threshold_robustness.csv", index=False)

    return {"best_model": best_name, "metrics": results, "train_rows": len(X_train), "test_rows": len(X_test)}


def main() -> None:
    setup()
    df = build_department_year_dataset()
    eda = run_eda(df)
    clustering = run_clustering(df)
    classification = run_classification(df)
    summary = {"eda": eda, "clustering": clustering, "classification": classification}
    (TABLES / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
