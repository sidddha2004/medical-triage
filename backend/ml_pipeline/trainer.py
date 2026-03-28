"""
ML Pipeline for Health Triage Assistant

Trains an XGBoost classifier on symptom-disease data.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score, accuracy_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import joblib


class SymptomClassifier:
    """XGBoost classifier for symptom-based disease prediction."""

    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.symptom_columns = []
        self.precautions_map = {}
        self.is_fitted = False

    def load_data(self, data_dir: str):
        """Load and combine symptom and precaution data."""

        symptoms_path = os.path.join(data_dir, 'DiseaseAndSymptoms.csv')
        precautions_path = os.path.join(data_dir, 'Disease precaution.csv')

        # Load symptoms data
        symptoms_df = pd.read_csv(symptoms_path)

        # Load precautions data
        precautions_df = pd.read_csv(precautions_path)

        return symptoms_df, precautions_df

    def preprocess(self, symptoms_df: pd.DataFrame, precautions_df: pd.DataFrame):
        """Clean and preprocess the data."""

        # Clean column names
        symptoms_df.columns = symptoms_df.columns.str.strip()
        precautions_df.columns = precautions_df.columns.str.strip()

        # Drop rows with missing disease names
        symptoms_df = symptoms_df.dropna(subset=['Disease'])
        precautions_df = precautions_df.dropna(subset=['Disease'])

        # Clean disease names
        symptoms_df['Disease'] = symptoms_df['Disease'].str.strip()
        precautions_df['Disease'] = precautions_df['Disease'].str.strip()

        # Get symptom columns (all columns except 'Disease')
        self.symptom_columns = [col for col in symptoms_df.columns if col != 'Disease']

        # Fill NaN symptoms with empty string (no symptom)
        symptoms_df[self.symptom_columns] = symptoms_df[self.symptom_columns].fillna('')

        # Build precautions map
        precaution_cols = [col for col in precautions_df.columns if col != 'Disease']
        for _, row in precautions_df.iterrows():
            disease = row['Disease']
            precs = [str(row[col]).strip() for col in precaution_cols if pd.notna(row[col]) and str(row[col]).strip()]
            self.precautions_map[disease] = precs

        # Remove duplicates based on disease + symptoms combination
        symptoms_df = symptoms_df.drop_duplicates(subset=['Disease'] + self.symptom_columns)

        return symptoms_df

    def create_features(self, df: pd.DataFrame):
        """Convert symptoms to binary features."""

        # Create binary matrix for symptoms
        all_symptoms = set()
        for col in self.symptom_columns:
            all_symptoms.update(df[col].unique())

        # Remove empty string
        all_symptoms.discard('')
        all_symptoms = sorted(list(all_symptoms))

        # Create symptom to index mapping for faster lookup
        symptom_to_idx = {symptom: idx for idx, symptom in enumerate(all_symptoms)}

        # Create binary features
        feature_matrix = np.zeros((len(df), len(all_symptoms)))

        # Reset index to match matrix rows
        df_reset = df.reset_index(drop=True)

        for idx, row in df_reset.iterrows():
            for col in self.symptom_columns:
                symptom = row[col]
                if symptom and symptom in symptom_to_idx:
                    symptom_idx = symptom_to_idx[symptom]
                    feature_matrix[idx, symptom_idx] = 1

        return feature_matrix, all_symptoms

    def train(self, data_dir: str = None):
        """Train the XGBoost classifier."""

        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

        print("Loading data...")
        symptoms_df, precautions_df = self.load_data(data_dir)

        print("Preprocessing...")
        df = self.preprocess(symptoms_df, precautions_df)

        print("Creating features...")
        X, self.all_symptoms = self.create_features(df)

        # Encode labels
        y = self.label_encoder.fit_transform(df['Disease'])

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        print(f"Number of diseases: {len(self.label_encoder.classes_)}")

        # Train XGBoost
        print("Training XGBoost classifier...")
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='multi:softprob',
            eval_metric='mlogloss',
            random_state=42,
            use_label_encoder=False
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')

        print(f"\n=== Model Performance ===")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"F1 Score (weighted): {f1:.4f}")
        print(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")

        self.is_fitted = True

        return {
            'accuracy': accuracy,
            'f1_score': f1,
            'num_diseases': len(self.label_encoder.classes_),
            'num_symptoms': len(self.all_symptoms),
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }

    def predict(self, symptoms: list):
        """Predict disease from symptoms list."""

        if not self.is_fitted:
            raise ValueError("Model not trained. Call train() first.")

        # Create feature vector
        feature_vector = np.zeros((1, len(self.all_symptoms)))
        for symptom in symptoms:
            symptom = symptom.strip().lower()
            # Try to match symptom (case-insensitive)
            for idx, known_symptom in enumerate(self.all_symptoms):
                if symptom in known_symptom.lower() or known_symptom.lower() in symptom:
                    feature_vector[0, idx] = 1
                    break

        # Predict
        pred_idx = self.model.predict(feature_vector)[0]
        proba = self.model.predict_proba(feature_vector)[0]

        disease = self.label_encoder.inverse_transform([pred_idx])[0]
        confidence = float(proba[pred_idx])

        # Get precautions
        precautions = self.precautions_map.get(disease, [])

        return {
            'disease': disease,
            'confidence': confidence,
            'precautions': precautions,
            'matched_symptoms': [s for s in symptoms if any(s.lower() in known.lower() for known in self.all_symptoms)]
        }

    def save(self, model_dir: str = None):
        """Save model and encoders."""

        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

        os.makedirs(model_dir, exist_ok=True)

        # Save model
        model_path = os.path.join(model_dir, 'classifier.json')
        self.model.save_model(model_path)

        # Save encoders and metadata
        metadata = {
            'all_symptoms': self.all_symptoms,
            'label_classes': list(self.label_encoder.classes_),
            'precautions_map': self.precautions_map,
        }

        metadata_path = os.path.join(model_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Model saved to {model_dir}")

    def load(self, model_dir: str = None):
        """Load trained model."""

        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

        # Load model
        model_path = os.path.join(model_dir, 'classifier.json')
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)

        # Load metadata
        metadata_path = os.path.join(model_dir, 'metadata.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        self.all_symptoms = metadata['all_symptoms']
        self.label_encoder.classes_ = np.array(metadata['label_classes'])
        self.precautions_map = metadata['precautions_map']
        self.is_fitted = True

        print(f"Model loaded from {model_dir}")


def train_model():
    """Main training function."""

    classifier = SymptomClassifier()

    print("=" * 50)
    print("Health Triage ML Pipeline")
    print("=" * 50)

    metrics = classifier.train()

    print("\n=== Training Complete ===")
    print(f"Diseases: {metrics['num_diseases']}")
    print(f"Symptoms: {metrics['num_symptoms']}")
    print(f"Test Accuracy: {metrics['accuracy']:.2%}")
    print(f"Test F1 Score: {metrics['f1_score']:.2%}")

    # Save model
    classifier.save()

    # Test prediction
    print("\n=== Test Prediction ===")
    test_symptoms = ['itching', 'skin_rash']
    result = classifier.predict(test_symptoms)
    print(f"Symptoms: {test_symptoms}")
    print(f"Prediction: {result['disease']} (confidence: {result['confidence']:.2%})")
    print(f"Precautions: {result['precautions']}")

    return classifier


if __name__ == '__main__':
    train_model()
