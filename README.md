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
