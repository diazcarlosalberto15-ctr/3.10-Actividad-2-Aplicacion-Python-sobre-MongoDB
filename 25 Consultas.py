import argparse
import time

from bson import json_util
from pymongo import MongoClient
from pymongo.errors import PyMongoError

URI_DEFAULT = "mongodb://localhost:27017"
DB_DEFAULT = "BDAutos"


# Colección: makers (Embedding)
MAKERS = [
    {"_id": 1, "name": "Volkswagen", "fullName": "Volkswagen AG", "country": "Germany", "continent": "Europe",
     "models": [{"name": "Jetta"}, {"name": "Golf"}]},
    {"_id": 2, "name": "Toyota", "fullName": "Toyota Motor Corporation", "country": "Japan", "continent": "Asia",
     "models": [{"name": "Corolla"}, {"name": "Prius"}]},
    {"_id": 3, "name": "Ford", "fullName": "Ford Motor Company", "country": "USA", "continent": "America",
     "models": [{"name": "Mustang"}, {"name": "F-150"}]},
    {"_id": 4, "name": "Honda", "fullName": "Honda Motor Co.", "country": "Japan", "continent": "Asia",
     "models": [{"name": "Civic"}, {"name": "Accord"}]},
    {"_id": 5, "name": "Nissan", "fullName": "Nissan Motor Co.", "country": "Japan", "continent": "Asia",
     "models": [{"name": "Sentra"}, {"name": "GTR"}, {"name": "Altima"}]},
    {"_id": 6, "name": "Audi", "fullName": "Audi AG", "country": "Germany", "continent": "Europe",
     "models": [{"name": "A4"}]},
]

# Colección: cars (Linking)
CARS = [
    {"_id": 101, "makerId": 1, "model_name": "Jetta", "description": "Jetta 2.0", "year": 2024, "cylinders": 4, "hp": 150, "weight_lb": 3000, "accel_0_60_s": 8.5, "mpg": 36},
    {"_id": 102, "makerId": 1, "model_name": "Golf", "description": "Golf R 2.0t", "year": 2024, "cylinders": 4, "hp": 315, "weight_lb": 3300, "accel_0_60_s": 4.5, "mpg": 28},
    {"_id": 103, "makerId": 2, "model_name": "Prius", "description": "Prius Hybrid", "year": 2024, "cylinders": 4, "hp": 120, "weight_lb": 2900, "accel_0_60_s": 9.8, "mpg": 55},
    {"_id": 104, "makerId": 3, "model_name": "Mustang", "description": "Mustang GT", "year": 2023, "cylinders": 8, "hp": 450, "weight_lb": 3800, "accel_0_60_s": 4.2, "mpg": 19},
    {"_id": 105, "makerId": 3, "model_name": "F-150", "description": "F-150 Raptor", "year": 2022, "cylinders": 8, "hp": 400, "weight_lb": 5000, "accel_0_60_s": 5.5, "mpg": 15},
    {"_id": 106, "makerId": 4, "model_name": "Civic", "description": "Civic Si 1.5t", "year": 2023, "cylinders": 4, "hp": 200, "weight_lb": 2900, "accel_0_60_s": 6.8, "mpg": 38},
    {"_id": 107, "makerId": 4, "model_name": "Accord", "description": "Accord V6", "year": 2018, "cylinders": 6, "hp": 278, "weight_lb": 3400, "accel_0_60_s": 5.8, "mpg": 25},
    {"_id": 108, "makerId": 5, "model_name": "GTR", "description": "GTR 3.8t", "year": 2024, "cylinders": 6, "hp": 565, "weight_lb": 3900, "accel_0_60_s": 2.9, "mpg": 16},
]


def cargar_datos(db):
    """Borra y vuelve a crear las colecciones makers y cars."""
    db.makers.drop()
    db.cars.drop()
    db.makers.insert_many(MAKERS)
    db.cars.insert_many(CARS)



# CONSULTAS DEL PROYECTO

LOOKUP_MAKER = {"$lookup": {"from": "makers", "localField": "makerId", "foreignField": "_id", "as": "maker"}}
UNWIND_MAKER = {"$unwind": "$maker"}


def _find(num, titulo, desc, coleccion, filtro, proyeccion=None, orden=None):
    return {"num": num, "titulo": titulo, "descripcion": desc, "tipo": "find",
            "coleccion": coleccion, "filtro": filtro, "proyeccion": proyeccion, "orden": orden}


def _agg(num, titulo, desc, coleccion, pipeline):
    return {"num": num, "titulo": titulo, "descripcion": desc, "tipo": "aggregate",
            "coleccion": coleccion, "pipeline": pipeline}


CONSULTAS = [
    _find(1, "Autos 2024+ con al menos 35 mpg",
          "Obtener los autos de modelo 2024 en adelante con rendimiento de al menos 35 mpg. Mostrar sólo la "
          "descripción, el año y el rendimiento, ordenados de mayor a menor rendimiento.",
          "cars",
          {"year": {"$gte": 2024}, "mpg": {"$gte": 35}},
          {"description": 1, "year": 1, "mpg": 1, "_id": 0},
          [("mpg", -1)]),

    _agg(2, "Europeos de 4 cilindros y >= 250 hp",
         "Listar los autos de fabricantes europeos con motor de 4 cilindros y al menos 250 hp, mostrando "
         "descripción, país y potencia, ordenados por potencia descendente.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$match": {"maker.continent": "Europe", "cylinders": 4, "hp": {"$gte": 250}}},
             {"$project": {"_id": 0, "description": 1, "country": "$maker.country", "hp": 1}},
             {"$sort": {"hp": -1}},
         ]),

    _agg(3, "Autos turbo de fabricantes japoneses",
         "Contar cuántos autos de fabricantes japoneses tienen motor turbo, es decir, cuya descripción termina "
         "con la cilindrada seguida de \"t\" (por ejemplo \"1.5t\").",
         "cars", [
             LOOKUP_MAKER,
             {"$match": {"maker.country": "Japan", "description": {"$regex": "t$", "$options": "i"}}},
             {"$count": "autos_turbo_japoneses"},
         ]),

    _find(4, "Ligeros y rápidos, o V8 eficientes",
          "Encontrar los autos que cumplan cualquiera de estas condiciones: (a) pesan menos de 3000 lb y "
          "aceleran de 0 a 60 mph en menos de 9 s, o (b) tienen 8 o más cilindros y rinden al menos 19 mpg.",
          "cars",
          {"$or": [
              {"weight_lb": {"$lt": 3000}, "accel_0_60_s": {"$lt": 9}},
              {"cylinders": {"$gte": 8}, "mpg": {"$gte": 19}},
          ]}),

    _find(5, "Fabricantes con más de un modelo",
          "Obtener los fabricantes que comercializan más de una marca o línea de modelo, mostrando nombre, "
          "país y modelos.",
          "makers",
          {"models.1": {"$exists": True}},
          {"_id": 0, "name": 1, "country": 1, "models": 1}),

    _agg(6, "Marca distinta del fabricante",
         "Encontrar los autos cuya marca (model.name) es distinta del nombre de su grupo fabricante "
         "(maker.name). Mostrar descripción, marca y fabricante.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$match": {"$expr": {"$ne": ["$model_name", "$maker.name"]}}},
             {"$project": {"_id": 0, "description": 1, "marca": "$model_name", "fabricante": "$maker.name"}},
         ]),

    _agg(7, "Autos, mpg y hp promedio por país",
         "Calcular por país el número de autos, el rendimiento promedio y la potencia promedio (redondeados a "
         "1 decimal), ordenado por número de autos.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$group": {"_id": "$maker.country", "numAutos": {"$sum": 1},
                         "avgMpg": {"$avg": "$mpg"}, "avgHp": {"$avg": "$hp"}}},
             {"$project": {"numAutos": 1, "avgMpg": {"$round": ["$avgMpg", 1]},
                           "avgHp": {"$round": ["$avgHp", 1]}}},
             {"$sort": {"numAutos": -1}},
         ]),

    _agg(8, "Autos, marcas distintas y hp por fabricante",
         "Calcular para cada grupo fabricante el número de autos, el número de marcas distintas con autos "
         "registrados y la potencia promedio (redondeada a 1 decimal), ordenado por número de autos.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$group": {"_id": "$maker.name", "numAutos": {"$sum": 1},
                         "marcasDistintas": {"$addToSet": "$model_name"}, "avgHp": {"$avg": "$hp"}}},
             {"$project": {"numAutos": 1, "numMarcasDistintas": {"$size": "$marcasDistintas"},
                           "avgHp": {"$round": ["$avgHp", 1]}}},
             {"$sort": {"numAutos": -1}},
         ]),

    _agg(9, "Modelos por continente",
         "Contar cuántos modelos (marcas) hay por continente.",
         "makers", [
             {"$unwind": "$models"},
             {"$group": {"_id": "$continent", "total_modelos": {"$sum": 1}}},
             {"$project": {"_id": 0, "continente": "$_id", "total_modelos": 1}},
         ]),

    _agg(10, "Rangos de rendimiento (mpg)",
         "Clasificar los autos en rangos de rendimiento [0,20), [20,25), [25,30), [30,35), [35,40) y 40 o más, "
         "contando cuántos hay en cada rango y su peso promedio.",
         "cars", [
             {"$bucket": {"groupBy": "$mpg", "boundaries": [0, 20, 25, 30, 35, 40], "default": "40 o mas",
                          "output": {"total_autos": {"$sum": 1}, "peso_promedio": {"$avg": "$weight_lb"}}}},
             {"$project": {
                 "_id": 0,
                 "rango_mpg": {"$switch": {"branches": [
                     {"case": {"$eq": ["$_id", 0]}, "then": "[0,20)"},
                     {"case": {"$eq": ["$_id", 20]}, "then": "[20,25)"},
                     {"case": {"$eq": ["$_id", 25]}, "then": "[25,30)"},
                     {"case": {"$eq": ["$_id", 30]}, "then": "[30,35)"},
                     {"case": {"$eq": ["$_id", 35]}, "then": "[35,40)"},
                 ], "default": "40 o mas"}},
                 "total_autos": 1,
                 "peso_promedio": {"$round": ["$peso_promedio", 1]},
             }},
         ]),

    _agg(11, "Top 5 fabricantes por mpg (>= 8 autos)",
         "Obtener los 5 fabricantes con mayor rendimiento promedio, considerando solo aquellos con al menos 8 "
         "autos registrados. (Con los datos de ejemplo ningún fabricante llega a 8 autos, por lo que el "
         "resultado es vacío.)",
         "cars", [
             {"$group": {"_id": "$makerId", "total_autos": {"$sum": 1}, "rendimiento_promedio": {"$avg": "$mpg"}}},
             {"$match": {"total_autos": {"$gte": 8}}},
             {"$lookup": {"from": "makers", "localField": "_id", "foreignField": "_id", "as": "maker"}},
             {"$unwind": "$maker"},
             {"$project": {"_id": 0, "fabricante": "$maker.name", "total_autos": 1,
                           "rendimiento_promedio": {"$round": ["$rendimiento_promedio", 2]}}},
             {"$sort": {"rendimiento_promedio": -1}},
             {"$limit": 5},
         ]),

    _agg(12, "Categoría de rendimiento por continente",
         "Clasificar cada auto como \"Alta\" (mpg >= 30), \"Media\" (20 <= mpg < 30) o \"Baja\" (mpg < 20) y "
         "contar cuántos autos hay por continente y categoría.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$project": {"continente": "$maker.continent", "categoria": {"$switch": {"branches": [
                 {"case": {"$gte": ["$mpg", 30]}, "then": "Alta"},
                 {"case": {"$gte": ["$mpg", 20]}, "then": "Media"},
             ], "default": "Baja"}}}},
             {"$group": {"_id": {"continente": "$continente", "categoria": "$categoria"},
                         "total_autos": {"$sum": 1}}},
             {"$project": {"_id": 0, "continente": "$_id.continente", "categoria": "$_id.categoria",
                           "total_autos": 1}},
             {"$sort": {"continente": 1, "categoria": 1}},
         ]),

    _agg(13, "Autos por fabricante (incluye ceros)",
         "Desde la colección makers, obtener cuántos autos tiene registrados cada fabricante "
         "(incluidos los que tienen cero).",
         "makers", [
             {"$lookup": {"from": "cars", "localField": "_id", "foreignField": "makerId", "as": "autos"}},
             {"$project": {"_id": 0, "fabricante": "$name", "pais": "$country", "total_autos": {"$size": "$autos"}}},
             {"$sort": {"total_autos": -1}},
         ]),

    _agg(14, "Modelos sin autos registrados",
         "Encontrar los modelos del catálogo que no tienen ningún auto registrado.",
         "makers", [
             {"$unwind": "$models"},
             {"$lookup": {"from": "cars", "localField": "models.name", "foreignField": "model_name",
                          "as": "autos_registrados"}},
             {"$match": {"autos_registrados": {"$size": 0}}},
             {"$project": {"_id": 0, "fabricante": "$name", "pais": "$country",
                           "modelo_sin_registro": "$models.name"}},
             {"$sort": {"fabricante": 1, "modelo_sin_registro": 1}},
         ]),

    _agg(15, "Top 5 autos más potentes + fabricante",
         "Para los 5 autos más potentes, obtener su descripción, potencia y el nombre completo (fullName) de "
         "su fabricante.",
         "cars", [
             {"$sort": {"hp": -1}},
             {"$limit": 5},
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$project": {"_id": 0, "descripcion": "$description", "potencia": "$hp",
                           "fabricante": "$maker.fullName"}},
         ]),

    _agg(16, "Top 3 de mpg por continente",
         "Obtener, para cada continente, los 3 autos con mayor rendimiento (descripción y mpg).",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$setWindowFields": {"partitionBy": "$maker.continent", "sortBy": {"mpg": -1},
                                   "output": {"posicion": {"$documentNumber": {}}}}},
             {"$match": {"posicion": {"$lte": 3}}},
             {"$project": {"_id": 0, "continente": "$maker.continent", "descripcion": "$description", "mpg": 1}},
             {"$sort": {"continente": 1, "mpg": 1}},
         ]),

    _agg(17, "Modelo con más autos por fabricante",
         "Para cada fabricante con más de un modelo, determinar cuál de sus modelos tiene más autos "
         "registrados.",
         "makers", [
             {"$match": {"models.1": {"$exists": True}}},
             {"$lookup": {"from": "cars", "localField": "_id", "foreignField": "makerId", "as": "autos"}},
             {"$unwind": "$autos"},
             {"$group": {"_id": {"maker": "$name", "modelo": "$autos.model_name"}, "count": {"$sum": 1}}},
             {"$sort": {"count": -1}},
             {"$group": {"_id": "$_id.maker", "modeloTop": {"$first": "$_id.modelo"},
                         "numAutos": {"$first": "$count"}}},
         ]),

    _agg(18, "% de autos por continente",
         "Calcular el porcentaje que representa cada continente sobre el total de autos, con 2 decimales.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$group": {"_id": "$maker.continent", "total_autos": {"$sum": 1}}},
             {"$group": {"_id": None,
                         "continentes": {"$push": {"continente": "$_id", "total_autos": "$total_autos"}},
                         "gran_total": {"$sum": "$total_autos"}}},
             {"$unwind": "$continentes"},
             {"$project": {"_id": 0, "continente": "$continentes.continente",
                           "total_autos": "$continentes.total_autos",
                           "porcentaje": {"$round": [
                               {"$multiply": [{"$divide": ["$continentes.total_autos", "$gran_total"]}, 100]}, 2]}}},
             {"$sort": {"porcentaje": -1}},
         ]),

    _agg(19, "Mayor diferencia vs. promedio de sus cilindros",
         "Listar los 5 autos que más superan el rendimiento promedio de los autos con su mismo número de "
         "cilindros, mostrando ese promedio y la diferencia.",
         "cars", [
             {"$setWindowFields": {"partitionBy": "$cylinders",
                                   "output": {"promedio_cilindros": {"$avg": "$mpg"}}}},
             {"$project": {"_id": 0, "descripcion": "$description", "cilindros": "$cylinders", "mpg": 1,
                           "promedio_cilindros": {"$round": ["$promedio_cilindros", 2]},
                           "diferencia": {"$round": [{"$subtract": ["$mpg", "$promedio_cilindros"]}, 2]}}},
             {"$sort": {"diferencia": -1}},
             {"$limit": 5},
         ]),

    _agg(20, "Autos con 8+ cilindros por continente",
         "Calcular, por continente, el número de autos, cuántos tienen 8 o más cilindros y el porcentaje que "
         "representan (1 decimal).",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$group": {"_id": "$maker.continent", "total_autos": {"$sum": 1},
                         "autos_8_o_mas_cilindros": {"$sum": {"$cond": [{"$gte": ["$cylinders", 8]}, 1, 0]}}}},
             {"$project": {"_id": 0, "continente": "$_id", "total_autos": 1, "autos_8_o_mas_cilindros": 1,
                           "porcentaje": {"$round": [
                               {"$multiply": [{"$divide": ["$autos_8_o_mas_cilindros", "$total_autos"]}, 100]}, 1]}}},
         ]),

    _agg(21, "Potencia por cada 1000 lb (Top 10)",
         "Calcular la potencia por cada 1000 lb de peso y mostrar los 10 autos con mayor valor, junto con su "
         "país.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$project": {"_id": 0, "descripcion": "$description", "pais": "$maker.country",
                           "potencia_por_1000lb": {"$round": [
                               {"$multiply": [{"$divide": ["$hp", "$weight_lb"]}, 1000]}, 2]}}},
             {"$sort": {"potencia_por_1000lb": -1}},
             {"$limit": 10},
         ]),

    _agg(22, "Modelos con nombre distinto al fabricante",
         "Para cada fabricante, mostrar solo los modelos cuyo nombre es distinto al nombre del fabricante, "
         "descartando a los fabricantes que no tengan ninguno.",
         "makers", [
             {"$project": {"_id": 0, "fabricante": "$name",
                           "modelos_distintos": {"$filter": {"input": "$models.name", "as": "model_name",
                                                             "cond": {"$ne": ["$$model_name", "$name"]}}}}},
             {"$match": {"$expr": {"$gt": [{"$size": "$modelos_distintos"}, 0]}}},
         ]),

    _agg(23, "Resumen con $facet",
         "En una sola consulta, obtener: (a) el número de autos por continente, (b) el número de autos por "
         "cilindros y (c) las estadísticas globales de mpg (mínimo, máximo y promedio).",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$facet": {
                 "autos_por_continente": [
                     {"$group": {"_id": "$maker.continent", "total_autos": {"$sum": 1}}},
                     {"$project": {"_id": 0, "continente": "$_id", "total_autos": 1}},
                 ],
                 "autos_por_cilindros": [
                     {"$group": {"_id": "$cylinders", "total_autos": {"$sum": 1}}},
                     {"$sort": {"_id": 1}},
                     {"$project": {"_id": 0, "cilindros": "$_id", "total_autos": 1}},
                 ],
                 "estadisticas_globales_mpg": [
                     {"$group": {"_id": None, "min_mpg": {"$min": "$mpg"}, "max_mpg": {"$max": "$mpg"},
                                 "avg_mpg": {"$avg": "$mpg"}}},
                     {"$project": {"_id": 0, "min_mpg": 1, "max_mpg": 1,
                                   "avg_mpg": {"$round": ["$avg_mpg", 2]}}},
                 ],
             }},
         ]),

    _agg(24, "Ranking de potencia de autos alemanes",
         "Asignar a cada auto alemán su posición por potencia dentro de su país y mostrar los 5 primeros.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$match": {"maker.country": "Germany"}},
             {"$setWindowFields": {"partitionBy": "$maker.country", "sortBy": {"hp": -1},
                                   "output": {"posicion_potencia": {"$documentNumber": {}}}}},
             {"$match": {"posicion_potencia": {"$lte": 5}}},
             {"$project": {"_id": 0, "descripcion": "$description", "pais": "$maker.country",
                           "potencia": "$hp", "posicion_potencia": 1}},
             {"$sort": {"posicion_potencia": 1}},
         ]),

    _agg(25, "Auto más eficiente por fabricante europeo",
         "Obtener para cada fabricante europeo su auto más eficiente.",
         "cars", [
             LOOKUP_MAKER, UNWIND_MAKER,
             {"$match": {"maker.continent": "Europe"}},
             {"$sort": {"mpg": -1}},
             {"$group": {"_id": "$maker.name", "auto_mas_eficiente": {"$first": "$description"},
                         "mpg": {"$first": "$mpg"}}},
             {"$project": {"_id": 0, "fabricante": "$_id", "auto_mas_eficiente": 1, "mpg": 1}},
         ]),
]

def _json(obj, indent=2):
    return json_util.dumps(obj, indent=indent, ensure_ascii=False)


def ejecutar_consulta(db, q):
    t0 = time.perf_counter()
    if q["tipo"] == "find":
        cursor = db[q["coleccion"]].find(q["filtro"], q.get("proyeccion"))
        if q.get("orden"):
            cursor = cursor.sort(q["orden"])
        docs = list(cursor)
    else:
        docs = list(db[q["coleccion"]].aggregate(q["pipeline"]))
    return docs, (time.perf_counter() - t0) * 1000


def codigo_mongo(q):
    col = q["coleccion"]
    if q["tipo"] == "find":
        args = [_json(q["filtro"])]
        if q.get("proyeccion"):
            args.append(_json(q["proyeccion"]))
        txt = f"db.{col}.find(\n" + ",\n".join(args) + "\n)"
        if q.get("orden"):
            txt += f".sort({_json(dict(q['orden']), indent=None)})"
        return txt
    return f"db.{col}.aggregate({_json(q['pipeline'])})"


def formatear_resultado(docs):
    return _json(docs) if docs else "[]   (sin resultados)"

def main_consola(uri, dbname):
    try:
        cliente = MongoClient(uri, serverSelectionTimeoutMS=3000)
        cliente.admin.command("ping")
    except PyMongoError as e:
        print(f"No se pudo conectar a MongoDB: {e}")
        return
    db = cliente[dbname]
    print(f"Conectado a {uri} · base '{dbname}'")

    while True:
        print("\n=== BDAutos - Consultas MongoDB ===")
        for q in CONSULTAS:
            print(f"{q['num']:>3}. {q['titulo']}")
        print("  a. Ejecutar las 25      c. Cargar datos de ejemplo      q. Salir")
        op = input("\nElige una opción: ").strip().lower()

        if op == "q":
            break
        if op == "c":
            if input("Se borrarán 'makers' y 'cars'. ¿Continuar? (s/n): ").strip().lower() == "s":
                cargar_datos(db)
                print("Datos cargados.")
            continue

        if op == "a":
            seleccion = CONSULTAS
        elif op.isdigit() and 1 <= int(op) <= len(CONSULTAS):
            seleccion = [CONSULTAS[int(op) - 1]]
        else:
            print("Opción no válida.")
            continue

        for q in seleccion:
            print("\n" + "=" * 70)
            print(f"CONSULTA {q['num']}. {q['descripcion']}")
            print("=" * 70)
            try:
                docs, ms = ejecutar_consulta(db, q)
                print(formatear_resultado(docs))
                print(f"-- {len(docs)} documento(s), {ms:.1f} ms")
            except PyMongoError as e:
                print(f"ERROR: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BDAutos - Consultas MongoDB")
    parser.add_argument("--uri", default=URI_DEFAULT, help=f"URI de MongoDB (default: {URI_DEFAULT})")
    parser.add_argument("--db", default=DB_DEFAULT, help=f"Nombre de la base de datos (default: {DB_DEFAULT})")
    args = parser.parse_args()
    main_consola(args.uri, args.db)