# Solar energy production for Danish Power Plants

![Test and Deploy](https://github.com/KarimAlaaElDine/solar-energy-pred/actions/workflows/docker-push-image.yml/badge.svg)

This projects makes use of energy production data provided by Energinet of the Danish Ministry of Climate and Energy to make solar power production predictions in the DK2 energy zone in Denmark. 

This project predicts energy production for the next 8 days using data that is 10 days old. Therefore, while the model predicts future dates based on the latest available data, the predictions may appear as past dates in the current context. This approach helps validate model accuracy and improve future forecasting while also providing data that is not yet available even if it is for past dates.

# Application Structure

This application contains the following folders and files:

 - **app:**  final model's app created using FastAPI
    - **main.py:** the main app file containing the definitions for the end points
    - **model:** the location of the model and helper files
        - **conv1d_103_141_40days:** the model
        - **api_data.py:** contains helper functions to fetch and transform the data to be fed to the model
        - **model.py:** contains the model initialization and the prediction function

- **analysis.ipynb:** a notebook containing the full analysis of the data as well as the model creation and testing

# Usage

This app is intended to be run through **Docker** as follows:

 1. Go to the project directory. 
 2. Run `docker build -t  energy-prediction-app:latest`.
 3. Once the docker file is created, run `docker run -p 80:80 energy-prediction-app:latest`.

Once running, the `/predict` endpoint can be called to return a JSON in the format `{"forcast": forcast}` where `forcast` is the list of predictions in **KWh** for the next **8 days**.
