import pandas as pd, time
from tensorflow.keras.models import load_model

model = load_model("dl_model.h5")

while True:
    data = pd.read_csv("sensor_data.csv").tail(1)
    X = data[["pH","Turbidity","Temperature","TDS"]]

    pred = model.predict(X)

    if pred[0][0] > 0.7:
        print("🚨 HIGH RISK OUTBREAK ALERT!")
    else:
        print("✅ WATER SAFE")

    time.sleep(5)
