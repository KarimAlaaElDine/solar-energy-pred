from pathlib import Path
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam
from model.api_data import get_features

model_version = '0.1.0'

features = get_features()

BASE_DIR = Path(__file__).resolve(strict=True).parent

model = load_model(f'{BASE_DIR}/conv1d_103_141_40days', compile=False)



def predict_():
    
    model.compile(optimizer=Adam(), loss='mean_squared_error', run_eagerly=True)
    return model.predict(features).tolist()
