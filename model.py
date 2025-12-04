import pandas as pd
import numpy as np
import pickle

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor

from sklearn.metrics import r2_score

df = pd.read_csv("delhi_aqi.csv")

breakpoints = {
    "pm2_5": [(0,30,0,50),(31,60,51,100),(61,90,101,200),(91,120,201,300),
              (121,250,301,400),(251,500,401,500)],

    "pm10":  [(0,50,0,50),(51,100,51,100),(101,250,101,200),(251,350,201,300),
              (351,430,301,400),(431,600,401,500)],

    "no2":   [(0,40,0,50),(41,80,51,100),(81,180,101,200),(181,280,201,300),
              (281,400,301,400),(401,1000,401,500)],

    "so2":   [(0,40,0,50),(41,80,51,100),(81,380,101,200),(381,800,201,300),
              (801,1600,301,400),(1601,2000,401,500)],

    "co":    [(0,1,0,50),(1.1,2,51,100),(2.1,10,101,200),(10.1,17,201,300),
              (17.1,34,301,400),(34.1,50,401,500)],

    "o3":    [(0,50,0,50),(51,100,51,100),(101,168,101,200),(169,208,201,300),
              (209,748,301,400),(749,1000,401,500)],

    "nh3":   [(0,200,0,50),(201,400,51,100),(401,800,101,200),(801,1200,201,300),
              (1201,1800,301,400),(1801,3000,401,500)]
}


def calc_subindex(pollutant, value):
    for bp_low, bp_high, si_low, si_high in breakpoints[pollutant]:
        if bp_low <= value <= bp_high:
            return ((si_high - si_low) / (bp_high - bp_low)) * (value - bp_low) + si_low
    return None


def compute_aqi(row):
    sub = []
    for pollutant in breakpoints.keys():
        if pollutant in row and not pd.isna(row[pollutant]):
            si = calc_subindex(pollutant, row[pollutant])
            if si is not None:
                sub.append(si)
    return max(sub) if sub else None


df["AQI"] = df.apply(compute_aqi, axis=1)

X = df.drop(columns=["AQI", "date"])
y = df["AQI"]

numeric_features = X.columns

preprocessor = ColumnTransformer(
    transformers=[
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]), numeric_features)
    ]
)

models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=300, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(),
    "XGBoost": XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6)
}

results = {}

print("\n===== MODEL ACCURACIES (R² Score) =====")

for name, model in models.items():
    pipe = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    accuracy = r2_score(y_test, y_pred)
    results[name] = accuracy

    print(f"{name}: {accuracy:.4f}")

best_model_name = max(results, key=results.get)
best_accuracy = results[best_model_name]
best_model = models[best_model_name]

print(f"\nBest Model: {best_model_name} with Accuracy (R²): {best_accuracy:.4f}")

final_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", best_model)
])

final_pipeline.fit(X, y)

# Save the model
pickle.dump(final_pipeline, open("best_aqi_model1.pkl", "wb"))

print("\nModel saved as: best_aqi_model.pkl")