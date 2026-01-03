import random, csv, time

filename = "sensor_data.csv"

with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["pH", "Turbidity", "Temperature", "TDS", "Outbreak"])

while True:
    ph = round(random.uniform(5.5, 9.0), 2)
    turbidity = round(random.uniform(1, 10), 2)
    temp = round(random.uniform(20, 40), 2)
    tds = round(random.uniform(50, 500), 2)

    outbreak = 1 if (ph < 6.8 or turbidity > 5 or tds > 300) else 0

    with open(filename, "a", newline="") as f:
        csv.writer(f).writerow([ph, turbidity, temp, tds, outbreak])

    print("IoT Data:", ph, turbidity, temp, tds)
    time.sleep(3)
