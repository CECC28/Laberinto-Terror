# LABERINTO DEL TERROR - Documentacion Completa para IA

> **Proyecto universitario**: FIME, Semestre 5, Interaccion Humano-Computadora
> **Python 3.12.6** | **Pygame 2.6.1** | **OpenCV 5.0.0.93** | **PyInstaller 6.22.2**

---

## RESUMEN EJECUTIVO

Juego de terror 2D de laberinto controlado por mouse. El jugador naviga 3 niveles de dificultad creciente usando solo el cursor del mouse (que se oculta durante el juego). Hay enemigos, trampas, habilidades, sistema de screamers con webcam, y un sistema de iluminacion con oscuridad progresiva.

**Objetivo**: Llegar a la salida (cuadrado verde) de cada nivel sin morir. El jugador tiene 3 vidas.

---

## ESTRUCTURA DE ARCHIVOS

```
PROYEC-TITO/
  main.py          # Archivo principal: game loop, estados, camara, dibujo
  settings.py      # Todas las constantes, colores, matrices de niveles
  entities.py      # Jugador, Enemigos (Perseguidor, Invisible), Trampas, Screamer
  skills.py        # SkillManager (4 habilidades), CajaHabilidad, Decoy
  level.py         # Level (laberinto), LightingMask (oscuridad), EnemigosManager
  menu_bg.jpg      # Imagen de fondo del menu (627KB)
  build.bat        # Script para compilar con PyInstaller (NO USAR - usar comando manual)
  dist/            # Ejecutable compilado (generado por PyInstaller)
  build/           # Archivos temporales de compilacion
```

---

## ARCHIVOS EN DETALLE

### settings.py (142 lineas)

Todas las constantes del juego. Cualquier cambio de balance se hace aqui.

**Pantalla**:
- `ANCHO = 800`, `ALTO = 600` - Tamano de ventana
- `TAM_CELDA = 40` - Tamano de cada celda del laberinto en pixeles
- `FPS = 60` - Frames por segundo

**Jugador**:
- `VIDAS = 3` - Vidas iniciales
- `TAM_JUGADOR = 14` - Tamano del cuadrado del jugador en pixeles
- `VELOCIDAD_JUGADOR = 5.0` (no se usa directamente, el movimiento es por lerp)

**Enemigos** (velocidad por nivel):
- `VELOCIDAD_PERSEGUIDOR = [1.0, 1.8, 2.5]` - Nivel 1, 2, 3
- `VELOCIDAD_INVISIBLE = [0.0, 0.6, 0.9]` - Nivel 1 (no se mueve), 2, 3
- `ALFA_INVISIBLE = 40` - Transparencia del invisible
- `DISTANCIA_SEGURA_SPAWN = 180` - Radio minimo de spawn lejos del jugador

**Iluminacion**:
- `RADIO_LUZ_NIVEL_2 = 120` - Radio de luz en nivel 2
- `RADIO_LUZ_NIVEL_3 = 70` - Radio de luz en nivel 3
- `RADIO_LUZ_CEGUERA_NIVEL_1 = 90` - Radio cuando hay ceguera en nivel 1
- `INTERVALO_PARPADEO_MIN = 3000`, `INTERVALO_PARPADEO_MAX = 5000` - Flicker nivel 3

**Habilidades**:
- `DURACION_INMUNIDAD = 2.0` seg
- `DURACION_CONGELAMIENTO = 3.0` seg
- `DURACION_SONAR = 2.5` seg
- `DURACION_DECOY = 4.0` seg
- `CAJAS_POR_NIVEL = 2` - Cajas de habilidad por nivel
- `DECOY_TAM = 20`

**Debuffs**:
- `DURACION_DEBUFF = 4.0` seg
- `DEBUFF_SLOWDOWN = 1` - Ralentiza movimiento (lerp: 0.12 -> 0.04)
- `DEBUFF_BLINDNESS = 2` - Reduce radio de luz a 50%
- `DEBUFF_INVERTED = 3` - Invierte controles relativamente

**Estados del juego**:
- `MENU`, `OPCIONES`, `AYUDA` - Pantallas de menu
- `JUGANDO` - Jugando
- `TE_ENCONTRARON` - Pantalla de dano (1.5 seg)
- `SCREAMER` - Screamer con foto de webcam
- `GAME_OVER` - Muerte
- `VICTORIA` - Gano los 3 niveles

**Matrices de niveles** (`NIVEL_1`, `NIVEL_2`, `NIVEL_3`):
- 15x15 celdas cada uno
- `1` = pared, `0` = camino
- `NIVELES = [NIVEL_1, NIVEL_2, NIVEL_3]`
- Spawn: jugador en primera celda libre, salida en ultima celda libre

---

### entities.py (367 lineas)

#### clase Jugador (lineas 20-131)

Cuadrado verde de 14x14 pixeles que sigue al cursor del mouse.

**Movimiento** (metodo `actualizar`):
- Calcula delta = mouse_pos - jugador_pos
- Si `control_invertido`: delta se invierte relativamente a `_inversion_origen`
- Aplica lerp: `nuevo_pos = pos_actual + delta * lerp_factor`
  - Normal: `lerp = 0.12`
  - Con slowdown: `lerp = 0.04`
- Cap de velocidad: `max_move = TAM_CELDA // 4` (10 px) para no saltar paredes
- Verifica colision con paredes ANTES de mover (test_rect separado para X e Y)

**Debuffs** (diccionario `self.debuffs = {tipo: tiempo_fin}`):
- `aplicar_debuff(tipo)` - Guarda debuff con timestamp de expiracion
- `actualizar_debuffs()` - Elimina debuffs expirados, limpia proteccion post-danio
- `tiene_debuff(tipo)` - Retorna True si el debuff esta activo
- `recibir_danio()` - Retorna `(vidas, hubo_danio)`. Tiene proteccion de 0.5s post-hit

**Estados internos**:
- `self.inmunidad` - True cuando la skill de inmunidad esta activa (sincronizado desde SkillManager)
- `self.control_invertido` - True cuando tiene debuff de controles invertidos
- `self._inversion_origen` - Posicion del jugador al activarse el debuff invertido
- `self._proteccion_danio` - True durante 0.5s despues de recibir dano
- `self.vivo` - False cuando vidas <= 0

#### clase Perseguidor (lineas 133-192)

Enemigo rojo que persigue al jugador o a un decoy.

- Tamano: `TAM_CELDA - 10` (30x30 pixeles)
- Velocidad: variable por nivel (1.0, 1.8, 2.5)
- Colision predictiva: verifica 4 esquinas antes de mover
- Cuando congelado: cambia a color azul brillante `(50, 120, 255)`
- Decoy: si hay decoy activo, va hacia el decoy en lugar del jugador

#### clase Invisible (lineas 195-248)

Enemigo casi transparente que se acerca al jugador.

- Tamano: `TAM_CELDA - 10` (30x30 pixeles)
- Velocidad: 0.0 en nivel 1, 0.6 en nivel 2, 0.9 en nivel 3
- Alpha: 40 (muy transparente)
- Calcula "volumen" segun distancia (para efectos de sonido, no implementado)
- Colision predictiva de 4 esquinas igual que Perseguidor

#### clase Trampa (lineas 251-287)

Cuadrado morado oscuro que aplica debuff al contacto. NO quita vida.

- Tamano: `TAM_CELDA - 12` (28x28 pixeles)
- Color uniforme: `(70, 30, 90)` - no revela que debuff tiene
- Se desactiva al ser tocada (una sola vez)
- Aparece gradualmente (fade-in de 400ms)
- Tipo de debuff: aleatorio entre SLOWDOWN, BLINDNESS, INVERTED

#### clase ScreamerManager (lineas 290-367)

Maneja screamers y foto de webcam.

- `activar_screamer_pequeno()` - Pantalla roja "TE ENCONTRARON!" por 1.8s
- `activar_screamer_grande()` - Game over con foto de webcam (2.5s)
- `_tomar_foto_webcam()` - Toma foto con cv2, la guarda como `foto_webcam.jpg`, la convierte a superficie pygame
- Si no hay camara disponible, muestra "Sin camara disponible"

---

### skills.py (217 lineas)

#### clase SkillManager (lineas 13-171)

Gestiona las 4 habilidades del jugador.

**Habilidades**:
- `HAB_INMUNIDAD = 1` - 2s de invulnerabilidad total
- `HAB_CONGELAR = 2` - 3s congela todos los enemigos
- `HAB_SONAR = 3` - 2.5s sin oscuridad + resalta enemigos y salida
- `HAB_DECOY = 4` - 4s crea clon que atrae perseguidores

**Flujo**:
1. Jugador toca `CajaHabilidad` -> `equipar_aleatoria()` equipa 1 de 4
2. Jugador presiona click izquierdo -> `usar_habilidad(button, mouse_pos)` activa la equipada
3. Solo se puede tener 1 habilidad a la vez
4. Las habilidades se resetean al cambiar de nivel

**Cooldowns** (manejados por timestamp):
- `self.tiempo_inmunidad`, `self.tiempo_congelamiento`, etc.
- Se comparan con `pygame.time.get_ticks()`

#### clase Decoy (lineas 174-190)

Cuadrado naranja pulsante de 20x20 con anillo animado.

- Se dibuja en la posicion donde se hizo click (coordenadas del mundo, no pantalla)
- Los perseguidores van hacia `self.pos` del decoy en lugar del jugador

#### clase CajaHabilidad (lineas 193-217)

Cuadrado dorado pulsante de 22x22 con "?" en el centro.

- Se desactiva al ser tocada
- Spawnean 2 por nivel en celdas libres lejanas al jugador

---

### level.py (256 lineas)

#### clase Level (lineas 13-108)

Representa un nivel del laberinto.

**Inicializacion**:
- Recibe una matriz 15x15 (1=pared, 0=camino)
- Genera lista de `self.paredes` (Rects de pygame)
- Encuentra `self.celdas_libres` (centros de celdas vacias en pixeles)
- `self.posicion_inicio` = primera celda libre
- `self.posicion_salida` = ultima celda libre
- Pre-renderiza el mapa completo en `self._superficie_mapa`

**Metodos de colision**:
- `es_pared_xy(x, y)` - Verifica si una coordenada en pixeles es pared (basado en matriz)
- `colision_con_paredes(rect)` - Verifica si un Rect colisiona con alguna pared de `self.paredes`

**Spawn**:
- `obtener_celdas_libres_para_spawn(cantidad, excluir_pos)` - Retorna celdas libres aleatorias
- Excluye celdas dentro de `DISTANCIA_SEGURA_SPAWN` (180px) del jugador

#### clase LightingMask (lineas 110-195)

Sistema de iluminacion con oscuridad progresiva.

**Nivel 1**: Sin oscuridad (a menos que tenga ceguera, entonces radio=90)
**Nivel 2**: Oscuridad constante (alpha=210, radio=120)
**Nivel 3**: Oscuridad fuerte (alpha=245, radio=70) + parpadeo tipo foco descompuesto

**Flicker nivel 3**:
- Genera 8-15 fases aleatorias (30-120ms cada una, on/off)
- Termina con 200ms completamente apagado
- Intervalo entre flickers: 3-5 segundos
- Cuando parpadea encendido, la oscuridad se aligera (alpha -= 40)

**Implementacion tecnica**:
- Superficie `surf_mask` con SRCALPHA, tamano pantalla
- `fill((0, 0, 0, alpha))` para oscurecer todo
- `draw.circle((0, 0, 0, 0), mouse_pos, radio)` para hacer agujero transparente
- Se dibuja SOBRE la pantalla, no sobre la superficie de juego

#### clase EnemigosManager (lineas 198-256)

Crea y actualiza enemigos por nivel.

**Creados por nivel**:
| Elemento      | Nivel 1 | Nivel 2 | Nivel 3 |
|---------------|---------|---------|---------|
| Perseguidores | 1       | 2       | 2       |
| Invisibles    | 0       | 1       | 1       |
| Trampas       | 2       | 3       | 4       |

**Metodo `actualizar`**: Recibe `congelar=True/False` desde SkillManager, aplica a todos los enemigos.

---

### main.py (617 lineas)

Archivo principal. Contiene la clase `Game` y el game loop.

#### Flujo del juego

```
__init__()
  -> pygame.init()
  -> Crea pantalla, reloj, fuentes
  -> Carga menu_bg.jpg
  -> Estado inicial: MENU

ejecutar()
  -> while True: manejar_eventos() -> actualizar() -> dibujar() -> reloj.tick(60)
```

#### Maquina de estados

| Estado          | Que pasa                                              |
|-----------------|-------------------------------------------------------|
| MENU            | Muestra menu con imagen de fondo + 3 botones          |
| OPCIONES        | Volumen, pantalla completa                            |
| AYUDA           | Info completa del juego                                |
| JUGANDO         | Game loop completo: movimiento, colisiones, enemigos  |
| TE_ENCONTRARON  | Pantalla roja 1.5s, luego reinicia nivel               |
| SCREAMER        | Screamer con foto webcam, luego GAME_OVER              |
| GAME_OVER       | Click para volver al menu                              |
| VICTORIA        | Click para volver al menu                              |

#### Camara

- Centrada en el jugador: `camera_x = ANCHO // 2 - jugador.centerx`
- Clamp: si el mapa es menor que la pantalla, se centra
- Si es mayor, se limita a los bordes del mapa

#### Orden de dibujo (estado JUGANDO)

1. `superficie_juego.fill(NEGRO)` - Fondo negro
2. `level.dibujar()` - Laberinto pre-renderizado
3. Cajas de habilidad
4. Trampas
5. Invisibles
6. Perseguidores
7. Decoy (si existe)
8. Jugador
9. Blit `superficie_juego` a pantalla con offset de camara
10. Overlay de Sonar (si activo)
11. Mascara de oscuridad (si no hay sonar)
12. HUD (vidas, nivel, habilidades, debuffs, flecha de salida)

#### Control del mouse

- **Menu**: Mouse visible, click izquierdo en botones
- **Jugando**: Mouse OCULTO, movimiento por lerp, click izquierdo para habilidades
- **Game Over/Victoria**: Mouse visible, click para volver al menu

---

## SISTEMA DE DANNO Y PROTECCION

```
recibir_danio():
  Si tiene inmunidad (skill activa) -> no dano
  Si tiene proteccion (0.5s post-hit) -> no dano
  Sino: vidas -= 1, activar proteccion 0.5s
  Retorna (vidas, hubo_danio)
```

**Fuentes de dano**:
- Paredes: `level.colision_con_paredes(jugador.rect)` -> dano
- Perseguidores: `jugador.rect.colliderect(perseguidor.rect)` -> dano
- Invisibles: `jugador.rect.colliderect(invisible.rect)` -> dano

**Trampas NO dan dano**, solo aplican debuff.

---

## COMANDO DE COMPILACION (PyInstaller)

```bash
pyinstaller --onedir --windowed --name "Laberinto_del_Terror" --clean ^
    --exclude-module matplotlib --exclude-module scipy --exclude-module pandas ^
    --exclude-module PIL --exclude-module tkinter ^
    --noupx --hidden-import skills main.py
```

**NOTAS IMPORTANTES**:
- Usar `--onedir` (NO `--onefile`) para evitar problemas de antivirus
- `--hidden-import skills` es OBLIGATORIO porque PyInstaller no detecta `skills.py` importado dinamicamente
- `--noupx` reduce tamano del ejecutable
- La imagen `menu_bg.jpg` se copia manualmente al dist despues de compilar
- Windows Defender puede borrar el ejecutable como falso positivo -> agregar exclusion en `dist/`

---

## PROBLEMAS CONOCIDOS Y PENDIENTES

1. **Colision con paredes**: El jugador puede avanzar tocando paredes sin recibir dano inmediatamente. El sistema de proteccion post-danio (0.5s) puede causar que el jugador "ignore" paredes si se mueve continuamente en una direccion.

2. **Invertido**: El delta de movimiento se invierte relativamente a la posicion del jugador al activarse el debuff. Puede haber edge cases donde el jugador se mueva mas rapido de lo esperado.

3. **Sonar**: La habilidad sonar elimina completamente la oscuridad durante su duracion. No tiene penalty visual.

4. **Webcam**: Si no hay camara, simplemente no muestra foto. No hay fallback visual interesante.

---

## DEPENDENCIAS

```
pygame>=2.6.0
opencv-python>=5.0.0
pyinstaller>=6.0.0 (solo para compilar)
```

Instalar con:
```bash
pip install pygame opencv-python pyinstaller
```

---

## PARA OTRA IA: QUE HACER AL EDITAR

1. **Si editas `settings.py`**: Todos los archivos lo importan con `from settings import *`. Cualquier constante nueva esta disponible automaticamente.

2. **Si editas `entities.py`**: Verifica que los imports de `settings.py` estan. El `Jugador` es la clase mas compleja - tiene movimiento, debuffs, y proteccion.

3. **Si editas `level.py`**: La clase `Level` maneja el laberinto. `LightingMask` es independiente. `EnemigosManager` crea enemigos basado en el nivel.

4. **Si editas `skills.py`**: El `SkillManager` se sincroniza con `main.py` linea 252: `self.jugador.inmunidad = self.skill_manager.inmunidad_activa`.

5. **Si editas `main.py`**: Es el centro de todo. El game loop esta en `ejecutar()`. Los estados se manejan en `actualizar()` y `dibujar()`.

6. **Despues de editar**: Correr `python -m py_compile archivo.py` para verificar sintaxis, luego rebuild con el comando de PyInstaller.

7. **NO usar `build.bat`**: Esta desactualizado. Usar el comando de PyInstaller directamente.
