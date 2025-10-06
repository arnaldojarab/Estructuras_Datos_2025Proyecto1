# Courier Quest

## Cómo ejecutar
```bash
python -m src
```

## Requisitos
- Python 3.10+
- Instalar dependencias:
```bash
pip install -r requirements.txt
```

# Estructuras de datos utilizadas

## Pedidos

La lógica de los pedidos se divide en 3 archivos:

1. **job_logic**: Coordina el flujo de los pedidos en el juego y los dibuja en pantalla. Interactúa con `job_loader` y `job_manager` para manejar los pedidos.
2. **job_loader**: Carga y mantiene un repositorio **único** de objetos `Job` (para evitar duplicados).
3. **job_manager**: Administra las estructuras de datos de los pedidos y las operaciones clave.

### Estructuras encontradas en `job_logic`

- **pickup_markers**: Lista de puntos o marcadores en pantalla donde aparecen los puntos de “recogida” visibles.  
- **dropoff_markers**: Lista de puntos o marcadores en pantalla donde aparecerán los puntos de “entrega” aceptados.

### Estructuras encontradas en `job_loader`

- **_jobs**: Cuando se hace el *fetch* de datos, se almacenan todos los pedidos del API en este **diccionario**, donde se guardan los objetos `Job` así: `{ "id_job": job }`.  
  De esta manera se puede acceder al job por medio del id. Esto permite, en próximas estructuras, almacenar solo el id y no duplicar los objetos `Job` en cada estructura que se necesite en un orden diferente.

### Estructuras encontradas en `job_manager`

- **release_queue**: **Cola** de ids de jobs que controla el orden en el que se van lanzando pedidos para que el jugador los pueda aceptar o no.  
- **_base_ids_sorted**: **Lista** (copia) de todos los ids de los jobs; es útil para realizar varias acciones, pero principalmente para poder rellenar la cola `release_queue` cuando esta se queda sin pedidos.  
- **history**: **Lista** de todos los trabajos que se han lanzado; guarda información relevante en cada entrada, como el id del job, si se aceptó o no, y si se entregó a tiempo.  
- **inventory**: **Lista** de ids de los jobs que el jugador sí aceptó y debe entregar. Cuando se entregan, salen del inventario y se registran en el historial. Con la tecla **E** se puede entrar a una interfaz gráfica donde es posible ver y modificar el orden del inventario.

### Estructura de datos usada en player.py:
**pos_history:
La estructura de datos usada para player fue una pila implementada mediante deque, esta cola se uso para almacenar las posiciones del jugador para poder hacer un deshacer o “undo( )” más adelante. Se uso una pila porque se requería devolver las últimas posiciones en las que estuvo y luego las primeras hasta llegar a la primera posición. 

## Mapa

La lógica del mapa se divide en dos partes: MapLoader, que se encarga de la información del mapa y sus características, y TileRenderer, cuya función es darle un aspecto agradable al mapa.

### Estructuras de datos usadas en TileRenderer:

- **cache**: Es un diccionario que se utiliza como caché con imágenes cargadas según el símbolo y la variante de la imagen. La clave en este diccionario es una tupla que contiene el símbolo y la variante específica para cada tile.
El acceso a la imagen es O(1) y no se necesitan operaciones de modificación o eliminación.

### Estructuras de datos usadas en MapLoader:

- **tiles**: Es una lista anidada que almacena, para cada posición del mapa, el símbolo y la variante de imagen correspondiente, por lo que `tiles[y][x] = [símbolo, variante]`.
El acceso directo a tiles por coordenadas tiene una complejidad algorítmica de O(1).
No se necesita modificar nada después de cargar el mapa.

## Clima

La lógica del clima se divide en tres clases: WeatherManager, que maneja la lógica del cambio de climas y la duración de cada uno; WeatherVisuals, encargado de mostrar los efectos visuales de cada clima; y Cloud, que es usado por WeatherVisuals para dar dinamismo a ciertos climas.

### Estructuras de datos usadas en WeatherVisuals:
- **clouds**: Es una lista que almacena los objetos Cloud que están activos.
- **wind_gusts**: Es una lista que almacena datos sobre los efectos de las ráfagas de viento; cada ráfaga es otra lista de atributos: `[x, y, speed, length, thickness, phase, freq, amp]`.

## Game Over Menu

### Estructuras encontradas en `game_over`

- **_rows**: Lista de diccionarios que guardan informacion sobre los 3 jugadores con los mejores puntajes y el jugador actual. 
