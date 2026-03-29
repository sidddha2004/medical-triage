"""
Inference Service - gRPC ML Inference with Caching
"""
import grpc
from concurrent import futures
import hashlib
import time
import os

import inference_pb2
import inference_pb2_grpc


class InferenceServiceServicer(inference_pb2_grpc.InferenceServiceServicer):
    """gRPC Inference Service with caching."""

    def __init__(self):
        self.model = None
        self.encoder = None
        self.loaded_version = None
        self.cache = {}
        self.load_model()

    def load_model(self):
        """Load ML model from disk."""
        import joblib
        model_path = os.environ.get('MODEL_PATH', '/app/models/classifier.joblib')
        encoder_path = os.environ.get('ENCODER_PATH', '/app/models/encoder.joblib')

        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            self.loaded_version = 'v1.0'
            print(f'Model loaded: {model_path}')
        except Exception as e:
            print(f'Error loading model: {e}')
            self.model = None

    def _get_cache_key(self, symptoms):
        """Generate cache key from sorted symptoms."""
        sorted_symptoms = sorted(symptoms)
        key_str = '|'.join(sorted_symptoms)
        return hashlib.md5(key_str.encode()).hexdigest()

    def Predict(self, request, context):
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._get_cache_key(request.symptoms)
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                return inference_pb2.PredictResponse(
                    success=True,
                    disease=cached['disease'],
                    confidence=cached['confidence'],
                    matched_symptoms=cached['matched_symptoms'],
                    precautions=cached['precautions'],
                    model_version=cached['model_version'],
                    latency_ms=(time.time() - start_time) * 1000,
                    cache_hit=True
                )

            # Run inference
            if self.model is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                return inference_pb2.PredictResponse(
                    success=False,
                    error='Model not loaded'
                )

            # Encode symptoms
            symptom_vector = self.encoder.transform([request.symptoms])

            # Predict
            prediction = self.model.predict(symptom_vector)[0]
            probabilities = self.model.predict_proba(symptom_vector)[0]
            confidence = float(max(probabilities))

            # Cache result
            result = {
                'disease': prediction,
                'confidence': confidence,
                'matched_symptoms': list(request.symptoms),
                'precautions': self._get_precautions(prediction),
                'model_version': self.loaded_version
            }
            self.cache[cache_key] = result

            return inference_pb2.PredictResponse(
                success=True,
                disease=prediction,
                confidence=confidence,
                matched_symptoms=list(request.symptoms),
                precautions=result['precautions'],
                model_version=self.loaded_version,
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=False
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return inference_pb2.PredictResponse(
                success=False,
                error=str(e)
            )

    def BatchPredict(self, request, context):
        try:
            predictions = []
            for req in request.requests:
                pred = self.Predict(req, context)
                predictions.append(pred)

            return inference_pb2.BatchPredictResponse(
                success=True,
                predictions=predictions
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return inference_pb2.BatchPredictResponse(
                success=False,
                error=str(e)
            )

    def GetModelStatus(self, request, context):
        try:
            return inference_pb2.ModelStatusResponse(
                loaded=self.model is not None,
                model_version=self.loaded_version or '',
                total_diseases=len(self.model.classes_) if self.model else 0,
                total_symptoms=len(self.encoder.categories_[0]) if self.encoder else 0,
                last_trained='2026-03-28'
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return inference_pb2.ModelStatusResponse(
                loaded=False,
                error=str(e)
            )

    def _get_precautions(self, disease):
        """Get precautions for a disease."""
        precautions_map = {
            'Flu': ['Rest', 'Hydrate', 'Isolate'],
            'Migraine': ['Rest in dark room', 'Hydrate', 'Avoid triggers'],
            'Common Cold': ['Rest', 'Hydrate', 'Over-the-counter medication'],
        }
        return precautions_map.get(disease, ['Consult a healthcare provider'])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceServiceServicer(), server
    )
    server.add_insecure_port('[::]:50053')
    server.start()
    print('Inference Service started on port 50053')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
