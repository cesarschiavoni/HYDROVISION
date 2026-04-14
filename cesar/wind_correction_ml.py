"""
Correccion de CWSI por viento mediante Machine Learning  [C2]
HydroVision AG — TRL 3-4

Entrena un modelo Random Forest / XGBoost que aprende la relacion:
  psi_stem_real = f(cwsi_raw, wind_ms, rad_wm2, vpd, t_air, hora_del_dia)

usando las sesiones Scholander como ground truth (4 sesiones OED, ~800 obs).

El modelo aprende implicitamente la correccion por viento sin necesidad de
modelar la fisica explicita. La literatura muestra R2 de 0.85-0.92 con ML
vs. 0.66 con CWSI lineal (Pires et al. 2025; Zhou et al. 2022).

Flujo:
  1. Recolectar datos de sesiones Scholander (psi_stem + payload nodo)
  2. Entrenar modelo con cross-validation
  3. Exportar modelo serializado (joblib) para uso en backend FastAPI
  4. En cada ingesta MQTT, corregir CWSI o predecir psi_stem directamente

Uso:
  trainer = WindCorrectionTrainer()
  trainer.load_scholander_data("ciencia/datos_scholander.csv")
  trainer.train()
  trainer.save("cesar/models/wind_correction_rf.joblib")

  predictor = WindCorrectionPredictor("cesar/models/wind_correction_rf.joblib")
  psi_pred = predictor.predict(cwsi=0.45, wind_ms=8.0, rad_wm2=750,
                                vpd=2.1, t_air=32.0, hour=13.5)

Referencias:
  Pires, A. et al. (2025). Scalable thermal imaging and processing framework
    for water status monitoring in vineyards. C&E in Agriculture, 239.
  Zhou, Z. et al. (2022). Ground-Based Thermal Imaging for Assessing Crop
    Water Status in Grapevines. Agronomy, 12(2), 322.
"""

import numpy as np
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class WindCorrectionSample:
    """Una observacion para entrenamiento: payload del nodo + Scholander."""
    cwsi_raw: float         # CWSI del nodo (con mitigaciones existentes)
    wind_ms: float          # velocidad del viento [m/s]
    rad_wm2: float          # radiacion solar [W/m2]
    vpd: float              # deficit de presion de vapor [kPa]
    t_air: float            # temperatura del aire [C]
    hour: float             # hora del dia [0-24)
    jones_ig: float = -1.0  # indice Jones (-1 = no disponible)
    quality_score: float = 100.0  # quality score del nodo [0-100]
    muller_gbh: float = 0.0      # gbh Muller [m/s]
    psi_stem: float = 0.0        # ground truth Scholander [MPa]


class WindCorrectionTrainer:
    """
    Entrena modelo de correccion de CWSI por viento.

    Features: cwsi_raw, wind_ms, rad_wm2, vpd, t_air, hour,
              jones_ig, quality_score, muller_gbh, wind_ms^2
    Target: psi_stem (Scholander)
    """

    FEATURE_NAMES = [
        "cwsi_raw", "wind_ms", "rad_wm2", "vpd", "t_air", "hour",
        "jones_ig", "quality_score", "muller_gbh", "wind_ms_sq",
    ]

    def __init__(self, model_type: str = "random_forest"):
        """
        model_type: 'random_forest' o 'xgboost' (si disponible).
        """
        self.model_type = model_type
        self.model = None
        self.samples: list[WindCorrectionSample] = []
        self.metrics: dict = {}

    def add_sample(self, sample: WindCorrectionSample):
        self.samples.append(sample)

    def load_scholander_data(self, csv_path: str):
        """
        Carga datos de sesiones Scholander desde CSV.
        Columnas esperadas: cwsi_raw, wind_ms, rad_wm2, vpd, t_air, hour,
                           jones_ig, quality_score, muller_gbh, psi_stem
        """
        import csv
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.add_sample(WindCorrectionSample(
                    cwsi_raw=float(row["cwsi_raw"]),
                    wind_ms=float(row["wind_ms"]),
                    rad_wm2=float(row["rad_wm2"]),
                    vpd=float(row["vpd"]),
                    t_air=float(row["t_air"]),
                    hour=float(row["hour"]),
                    jones_ig=float(row.get("jones_ig", -1)),
                    quality_score=float(row.get("quality_score", 100)),
                    muller_gbh=float(row.get("muller_gbh", 0)),
                    psi_stem=float(row["psi_stem"]),
                ))

    def _build_features(self, samples: list[WindCorrectionSample]) -> np.ndarray:
        """Construye matriz de features con termino cuadratico de viento."""
        X = np.array([
            [s.cwsi_raw, s.wind_ms, s.rad_wm2, s.vpd, s.t_air, s.hour,
             s.jones_ig, s.quality_score, s.muller_gbh,
             s.wind_ms ** 2]  # termino cuadratico: efecto no-lineal del viento
            for s in samples
        ])
        return X

    def train(self, test_size: float = 0.15, random_state: int = 42) -> dict:
        """
        Entrena el modelo con cross-validation.
        Retorna metricas de rendimiento.
        """
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.metrics import mean_squared_error, r2_score

        if len(self.samples) < 20:
            raise ValueError(
                f"Insuficientes muestras ({len(self.samples)}). "
                f"Minimo 20, recomendado 200+."
            )

        X = self._build_features(self.samples)
        y = np.array([s.psi_stem for s in self.samples])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        if self.model_type == "random_forest":
            from sklearn.ensemble import RandomForestRegressor
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=8, min_samples_leaf=5,
                random_state=random_state, n_jobs=-1,
            )
        elif self.model_type == "xgboost":
            from xgboost import XGBRegressor
            self.model = XGBRegressor(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=random_state,
            )
        else:
            raise ValueError(f"model_type '{self.model_type}' no soportado")

        self.model.fit(X_train, y_train)

        # Metricas
        y_pred = self.model.predict(X_test)
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring="r2")

        self.metrics = {
            "r2_test": float(r2_score(y_test, y_pred)),
            "rmse_test": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2_cv_mean": float(np.mean(cv_scores)),
            "r2_cv_std": float(np.std(cv_scores)),
            "n_samples": len(self.samples),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "feature_importance": dict(zip(
                self.FEATURE_NAMES,
                [float(fi) for fi in self.model.feature_importances_]
            )),
        }
        return self.metrics

    def save(self, path: str):
        """Guarda modelo serializado con joblib."""
        import joblib
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        joblib.dump({"model": self.model, "metrics": self.metrics,
                     "features": self.FEATURE_NAMES}, path)

    def load(self, path: str):
        """Carga modelo desde archivo joblib."""
        import joblib
        data = joblib.load(path)
        self.model = data["model"]
        self.metrics = data["metrics"]


class WindCorrectionPredictor:
    """
    Predictor de psi_stem corregido por viento.
    Usa el modelo entrenado por WindCorrectionTrainer.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.metrics: dict = {}
        if model_path and os.path.exists(model_path):
            import joblib
            data = joblib.load(model_path)
            self.model = data["model"]
            self.metrics = data.get("metrics", {})

    @property
    def is_ready(self) -> bool:
        return self.model is not None

    def predict(self, cwsi_raw: float, wind_ms: float, rad_wm2: float,
                vpd: float, t_air: float, hour: float,
                jones_ig: float = -1.0, quality_score: float = 100.0,
                muller_gbh: float = 0.0) -> dict:
        """
        Predice psi_stem corregido por viento.

        Retorna dict con psi_stem predicho y nivel hidrico.
        """
        if not self.is_ready:
            return {"psi_stem_ml": None, "status": "modelo_no_cargado"}

        X = np.array([[cwsi_raw, wind_ms, rad_wm2, vpd, t_air, hour,
                        jones_ig, quality_score, muller_gbh,
                        wind_ms ** 2]])

        psi = float(self.model.predict(X)[0])

        if psi > -0.60:
            nivel = "SIN_ESTRES"
        elif psi > -1.00:
            nivel = "ESTRES_LEVE"
        elif psi > -1.40:
            nivel = "ESTRES_MODERADO_SEVERO"
        else:
            nivel = "ESTRES_CRITICO"

        return {
            "psi_stem_ml": round(psi, 3),
            "nivel_hidrico_ml": nivel,
            "model_r2": self.metrics.get("r2_cv_mean"),
            "status": "ok",
        }
