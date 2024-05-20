from fastapi import FastAPI
from pydantic import BaseModel
from model.model import predict_

app = FastAPI()



class PredictionOut(BaseModel):
    forcast: list


@app.get("/")
def home():
    return {"site_active": "True"}

@app.get("/predict", response_model=PredictionOut)
def predict():
    forcast = predict_()

    return {"forcast": forcast}



