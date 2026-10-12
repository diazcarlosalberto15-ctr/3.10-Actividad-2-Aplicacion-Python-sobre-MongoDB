# BDAutos - Consultas MongoDB en Python

Aplicación de consola en Python que ejecuta las 25 consultas del proyecto **BDAutos** sobre las colecciones `makers` y `cars` de MongoDB.

- Carlos Alberto Diaz Sanchez #385539

## Colecciones

- **makers** (embedding): fabricantes con su país, continente y la lista de modelos incrustada (6 documentos).
- **cars** (linking): autos con año, cilindros, potencia, peso, aceleración y rendimiento; se relacionan con su fabricante mediante `makerId` (8 documentos).

## Requisitos

- Python 3.8 o superior
- MongoDB 5.0 o superior (las consultas 16, 19 y 24 usan `$setWindowFields`)
- Librería `pymongo`

## Instalación

```bash
pip install pymongo
```

## Uso

```bash
python 25_Consultas.py
```

Por defecto se conecta a `mongodb://localhost:27017` y usa la base `BDAutos`. Para cambiarlo:

```bash
python 25_Consultas.py --uri mongodb://usuario:clave@host:27017 --db BDAutos
```

### Menú

| Opción | Acción |
|--------|--------|
| `1` a `25` | Ejecuta esa consulta |
| `a` | Ejecuta las 25 consultas seguidas |
| `c` | Carga los datos de ejemplo (borra y recrea `makers` y `cars`) |
| `q` | Sale |

La primera vez conviene usar `c` para cargar las colecciones antes de ejecutar las consultas.

## Consultas

1. Autos 2024+ con al menos 35 mpg
2. Europeos de 4 cilindros y >= 250 hp
3. Autos turbo de fabricantes japoneses
4. Ligeros y rápidos, o V8 eficientes
5. Fabricantes con más de un modelo
6. Marca distinta del fabricante
7. Autos, mpg y hp promedio por país
8. Autos, marcas distintas y hp por fabricante
9. Modelos por continente
10. Rangos de rendimiento (mpg)
11. Top 5 fabricantes por mpg (>= 8 autos)
12. Categoría de rendimiento por continente
13. Autos por fabricante (incluye ceros)
14. Modelos sin autos registrados
15. Top 5 autos más potentes + fabricante
16. Top 3 de mpg por continente
17. Modelo con más autos por fabricante
18. % de autos por continente
19. Mayor diferencia vs. promedio de sus cilindros
20. Autos con 8+ cilindros por continente
21. Potencia por cada 1000 lb (Top 10)
22. Modelos con nombre distinto al fabricante
23. Resumen con $facet
24. Ranking de potencia de autos alemanes
25. Auto más eficiente por fabricante europeo

## Notas

- La consulta 11 devuelve un resultado vacío con los datos de ejemplo, porque ningún fabricante tiene 8 autos registrados.
- En la consulta 23 el `$round` se aplica en un `$project` posterior al `$group`, ya que MongoDB no permite usarlo dentro del `$group`.