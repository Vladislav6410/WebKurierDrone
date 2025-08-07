"""
Парсер телеметрии дронов. Преобразует входные RAW-данные в структурированный формат.
"""

def parse(raw_data):
    """
    Пример входных данных:
    "GPS:52.1,13.4;ALT:120;BAT:87%"
    """
    try:
        parts = raw_data.split(";")
        telemetry = {}
        for part in parts:
            key, value = part.split(":")
            telemetry[key.strip().lower()] = value.strip()
        return telemetry
    except Exception as e:
        return {"error": str(e)}

# Пример использования:
if __name__ == "__main__":
    sample = "GPS:52.1,13.4;ALT:120;BAT:87%"
    print(parse(sample))
