import pickle


def calculate_heat_index_custom_celsius(temperature, relative_humidity):
    c1 = -8.785
    c2 = 1.611
    c3 = 2.339
    c4 = -0.146
    c5 = -0.01231
    c6 = -0.01642
    c7 = .002212
    c8 = .0007255
    c9 = 0.000003582

    HI = (
            c1
            + c2 * temperature
            + c3 * relative_humidity
            + c4 * temperature * relative_humidity
            + c5 * temperature * temperature
            + c6 * relative_humidity * relative_humidity
            + c7 * temperature * temperature * relative_humidity
            + c8 * temperature * relative_humidity * relative_humidity
            + c9 * temperature * temperature * relative_humidity * relative_humidity
    )
    return HI


def predict_ac_status(outside_temp, temperature, heat_index, light):
    # Previsão com base nos valores inseridos
    outside_temp = float(outside_temp)
    temperature = float(temperature)
    heat_index = float(heat_index)
    light = float(light)

    # Load the model from the file
    model_filename = './modules/ACStatus/random_forest_model.pkl'
    with open(model_filename, 'rb') as model_file:
        clf = pickle.load(model_file)

    prediction = clf.predict([[outside_temp, temperature, heat_index, light]])

    return prediction[0]
