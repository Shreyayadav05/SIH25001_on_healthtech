import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

data = pd.read_csv("sensor_data.csv")

X = data[["pH","Turbidity","Temperature","TDS"]]
y = data["Outbreak"]

model = Sequential([
    Dense(16, activation='relu', input_shape=(4,)),
    Dense(8, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(X, y, epochs=25, batch_size=8)

model.save("dl_model.h5")
print("Deep Learning Model Trained & Saved")
