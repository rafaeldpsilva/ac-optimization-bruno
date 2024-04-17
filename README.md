# TioCPS

## Quickstart

To quickly install all the needed dependencies run:

```
pip install -r reqs.txt
```

To start the application run [`main.py`](/api/main.py)

### Database Access

In order to change the database access you need to add the following file:

[config/config.json](./config/config.json) :

```
{
    "app": {
        "port" : 5002,
        "monitoring": 1
    },
    "storage" : {
        "_comment" : "database configuration using mongodb",
        "storing_frequency": 5,
        "local" : {
            "type" : "mongodb",
            "server" : "192.168.2.68",
            "port" : 27018,
            "database" : "BuildingRightSide",
            "iots_reading": ["BuildingRightSide", "iots_reading"],
            "forecast": ["Forecast","forecastvaluerightside"],
            "totalpower": ["TotalPower","powerrightside"],
	    "token": ["Tokens_rightside","tokencol"]
        }
    },
    "resources" : {
        "_comment" : "reading period in seconds, resource response",
        "monitoring_period" : 1,
        "iots" : [
            {
                "name" : "Fridge",
                "type" : "refrigerator",
                "uri" : "http://192.168.2.5:8520/enaplug/read/170307001",
                "method" : "GET",
                "body" : "",
                "values" : [
                    {
                        "type" : "power",
                        "tag" : "enaplug_170307001.act1",
                        "data" : "DOUBLE"
                    }
		],
                "control" : {
                    "type" : "none"
                },
                "store" : {
                    "period" : 10, 
                    "type" : "avg"
                } 
            }
	]
    }
}
```

### Notas Rafael

- criar novo mecanismo para ler configurações (em vez de ler todas as vezes, ler apenas no inicio)
