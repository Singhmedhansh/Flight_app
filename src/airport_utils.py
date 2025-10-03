def load_airport_cities():
    airport_cities = {}
    import csv, os
    csv_path = os.path.join(os.path.dirname(__file__), 'dataset', 'airports.csv')
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            airport_cities[row['code']] = row['city']
    return airport_cities
