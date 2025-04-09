import os
import json
import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

def train_model(df, model_name="default"):
    df.columns = ['ugpa','LSAT','lgpa','result'] 
    df.dropna(inplace=True)
    # Encode result column (PASS=1, else=0)
    df.loc[df['result'] == 'PASS', 'result'] = 1
    df.loc[df['result'] != 1, 'result'] = 0
    df['result'] = df['result'].astype(int)

    X = df[['lgpa', 'ugpa', 'LSAT']]
    y = df['result']

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pruned Decision Tree
    model = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=10,
        ccp_alpha=0.005,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate (optional)
    print("✅ Training complete")
    print(classification_report(y_test, model.predict(X_test)))

    # Save model
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, f"models/{model_name}.pkl")
    print(f"✅ Model saved to models/{model_name}.pkl")

