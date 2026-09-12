from __future__ import annotations

from pathlib import Path
import json
import re

import numpy as np
import pandas as pd
from unidecode import unidecode


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"


DEPT_REPLACEMENTS = {
    "PROV CONST DEL CALLAO": "CALLAO",
    "PROV. CONST. DEL CALLAO": "CALLAO",
    "REGION LIMA": "LIMA",
    "LIMA METROPOLITANA": "LIMA",
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = text.replace("�", "")
    text = unidecode(text)
    text = re.sub(r"[^A-Z0-9. ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return DEPT_REPLACEMENTS.get(text, text)


def normalize_department(value: object) -> str:
    text = normalize_text(value)
    repairs = {
        "NCASH": "ANCASH",
        "APURMAC": "APURIMAC",
        "HUNUCO": "HUANUCO",
        "JUNN": "JUNIN",
        "REGIN LIMA": "LIMA",
        "SAN MARTN": "SAN MARTIN",
    }
    return repairs.get(text, text)


def indicator_slug(value: str) -> str:
    text = normalize_text(value)
    if "CONFIANZA" in text:
        return "confianza_pnp_pct"
    if "INSEGURIDAD" in text:
        return "percepcion_inseguridad_pct"
    if "ESTAFA" in text:
        return "victimizacion_estafa_pct"
    if "ROBO" in text:
        return "victimizacion_robo_pct"
    if "VICTIMIZACI" in text or "VICTIMIZACION" in text:
        return "victimizacion_pct"
    return text.lower().replace(" ", "_")


def load_denuncias() -> pd.DataFrame:
    path = RAW / "denuncias_policiales_2018_2026_julio.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    df["departamento"] = df["DPTO_HECHO_NEW"].map(normalize_department)
    df["modalidad"] = df["P_MODALIDADES"].map(normalize_text)
    df["anio"] = df["ANIO"].astype(int)
    df["mes"] = df["MES"].astype(int)
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0).astype(int)
    return df


def load_enapres() -> pd.DataFrame:
    path = RAW / "victimizacion_percepcion_confianza_pnp_2013_2024.csv"
    df = pd.read_csv(path, encoding="latin1")
    df.columns = [c.strip() for c in df.columns]
    df["departamento"] = df["DEPARTAMENTO"].map(normalize_department)
    df["indicador"] = df["INDICADOR"].map(indicator_slug)
    df["anio"] = pd.to_numeric(df["VALOR PERIODO"], errors="coerce").astype("Int64")
    df["valor"] = pd.to_numeric(df["VALOR"], errors="coerce")
    df["ambito"] = df["AMBITO_PROY"].map(normalize_text)
    return df


def load_population() -> pd.DataFrame:
    path = RAW / "inei_poblacion_departamento_provincia_distrito_2018_2026.xlsx"
    raw = pd.read_excel(path, sheet_name=0, header=None)
    table = raw.iloc[6:, :11].copy()
    table.columns = ["ubigeo", "departamento", 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    table = table.dropna(subset=["ubigeo", "departamento"])
    table["ubigeo"] = table["ubigeo"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    dept = table[(table["ubigeo"].str.endswith("0000")) & (table["ubigeo"] != "000000")].copy()
    dept["departamento"] = dept["departamento"].map(normalize_department)
    long = dept.melt(id_vars=["ubigeo", "departamento"], var_name="anio", value_name="poblacion")
    long["anio"] = long["anio"].astype(int)
    long["poblacion"] = pd.to_numeric(long["poblacion"], errors="coerce")
    return long[["departamento", "anio", "poblacion", "ubigeo"]]


def entropy(values: pd.Series) -> float:
    total = values.sum()
    if total <= 0:
        return 0.0
    p = values[values > 0] / total
    return float(-(p * np.log(p)).sum())


def build_department_year_dataset() -> pd.DataFrame:
    INTERIM.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    denuncias = load_denuncias()
    enapres = load_enapres()
    population = load_population()

    den_dept = (
        denuncias.groupby(["departamento", "anio"], as_index=False)
        .agg(denuncias_total=("cantidad", "sum"), meses_observados=("mes", "nunique"))
    )
    den_dept["anio_completo"] = den_dept["meses_observados"].eq(12)

    modality = (
        denuncias.groupby(["departamento", "anio", "modalidad"], as_index=False)["cantidad"].sum()
        .pivot_table(index=["departamento", "anio"], columns="modalidad", values="cantidad", fill_value=0)
        .reset_index()
    )
    modality.columns.name = None
    modality = modality.rename(columns={c: f"denuncias_{c.lower().replace(' ', '_').replace('.', '')}" for c in modality.columns if c not in ["departamento", "anio"]})
    den = den_dept.merge(modality, on=["departamento", "anio"], how="left", validate="one_to_one")
    modality_cols = [c for c in den.columns if c.startswith("denuncias_") and c != "denuncias_total"]
    for col in modality_cols:
        den[f"prop_{col.replace('denuncias_', '')}"] = den[col] / den["denuncias_total"].replace(0, np.nan)
    den["diversidad_modalidades"] = den[modality_cols].apply(entropy, axis=1)

    en_dept = enapres[(enapres["ambito"] == "DEPARTAMENTO") & enapres["anio"].notna()].copy()
    en_pivot = (
        en_dept.pivot_table(
            index=["departamento", "anio"],
            columns="indicador",
            values="valor",
            aggfunc="mean",
        )
        .reset_index()
    )
    en_pivot.columns.name = None
    en_pivot["anio"] = en_pivot["anio"].astype(int)

    panel = den.merge(population, on=["departamento", "anio"], how="left", validate="many_to_one")
    panel["denuncias_tasa_100k"] = panel["denuncias_total"] / panel["poblacion"] * 100_000
    panel = panel.sort_values(["departamento", "anio"])
    panel["denuncias_tasa_100k_lag1"] = panel.groupby("departamento")["denuncias_tasa_100k"].shift(1)
    panel["denuncias_total_lag1"] = panel.groupby("departamento")["denuncias_total"].shift(1)
    panel["denuncias_tasa_yoy"] = panel.groupby("departamento")["denuncias_tasa_100k"].pct_change()

    integrated = panel.merge(en_pivot, on=["departamento", "anio"], how="inner", validate="one_to_one")
    integrated = integrated[(integrated["anio"] >= 2018) & (integrated["anio"] <= 2024)].copy()
    integrated = integrated.sort_values(["departamento", "anio"]).reset_index(drop=True)

    for col in [
        "victimizacion_pct",
        "percepcion_inseguridad_pct",
        "confianza_pnp_pct",
        "victimizacion_robo_pct",
        "victimizacion_estafa_pct",
    ]:
        if col in integrated:
            integrated[f"{col}_lag1"] = integrated.groupby("departamento")[col].shift(1)

    integrated["brecha_percepcion_victimizacion"] = (
        integrated["percepcion_inseguridad_pct"] - integrated["victimizacion_pct"]
    )
    integrated["victimizacion_alta_q75_anual"] = (
        integrated["victimizacion_pct"]
        >= integrated.groupby("anio")["victimizacion_pct"].transform(lambda s: s.quantile(0.75))
    ).astype(int)

    denuncias.to_csv(INTERIM / "denuncias_limpias.csv", index=False)
    enapres.to_csv(INTERIM / "enapres_limpia.csv", index=False)
    population.to_csv(INTERIM / "poblacion_departamento_anio.csv", index=False)
    panel.to_csv(INTERIM / "denuncias_departamento_anio.csv", index=False)
    en_pivot.to_csv(INTERIM / "enapres_departamento_anio.csv", index=False)
    integrated.to_csv(PROCESSED / "panel_departamento_anio_2018_2024.csv", index=False)

    merge_audit = {
        "denuncias_rows_raw": int(len(denuncias)),
        "enapres_rows_raw": int(len(enapres)),
        "population_rows_department_year": int(len(population)),
        "denuncias_department_year_rows": int(len(panel)),
        "enapres_department_year_rows": int(len(en_pivot)),
        "integrated_rows_2018_2024": int(len(integrated)),
        "integrated_departments": sorted(integrated["departamento"].unique()),
        "integrated_years": sorted(int(x) for x in integrated["anio"].unique()),
        "merge_level": "departamento-anio",
        "classification_target": "victimizacion_alta_q75_anual",
        "target_definition": "1 si victimización porcentual del departamento-año >= percentil 75 de su año.",
    }
    (TABLES / "merge_audit.json").write_text(json.dumps(merge_audit, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([merge_audit]).to_csv(TABLES / "merge_audit.csv", index=False)
    return integrated


if __name__ == "__main__":
    df = build_department_year_dataset()
    print(df.shape)
    print(df.head().to_string())
