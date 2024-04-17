import pandas as pd


class ForecastAdapter:
    def __init__(self):
        return

    def forecast_saved_model(self):
        from modules.forecast.save_model_forecast_consumption import forecast_consumption
        df = forecast_consumption()
        return df.values.tolist()
    
    def forecast_generation_saved_model(self):
        from modules.forecast.save_model_forecast_generation import forecast_generation
        return forecast_generation()

    def forecast_day_consumption(self, consumption):
        from modules.forecast.Forecast_Script_Consumption import ForecastDay_Cons

        consumption = consumption.rename(columns={'totalpower': 'Consumption', 'datetime': 'Periods'})
        consumption = pd.DataFrame(consumption, columns=['Periods', 'Consumption'])
        return ForecastDay_Cons(consumption)

    def forecast_consumption(self, consumption):
        from modules.forecast.consumption_forecast import consumption_forecast
        forecast = consumption_forecast(consumption)
        # building_repo.insert_forecastday(Pred.iat, datetime.datetime.now() + datetime.timedelta(minutes=45))
        return forecast
