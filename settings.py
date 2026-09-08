# -*- coding: utf-8 -*-
"""
settings.py - Constantes, colores, matrices de niveles y configuracion del juego.
"""

# ==================== PANTALLA ====================
ANCHO = 800
ALTO = 600
TAM_CELDA = 40
FPS = 60
TITULO = "LABERINTO DEL TERROR"

# ==================== COLORES ====================
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS_OSCURO = (30, 30, 30)
GRIS_CAMINO = (50, 50, 50)
GRIS_PARED = (80, 80, 80)
VERDE_JUGADOR = (0, 255, 80)
ROJO = (255, 0, 0)
ROJO_OSCURO = (150, 0, 0)
AZUL_INVISIBLE = (60, 60, 200)
MAGENTA_TRAMPA = (255, 0, 180)
DORADO = (255, 215, 0)
AMARILLO = (255, 255, 0)
NARANJA = (255, 140, 0)
VERDE_OSCURO = (0, 120, 0)
ROSA = (255, 80, 120)
CIAN = (0, 220, 220)

# ==================== JUGADOR ====================
VIDAS = 3
TAM_JUGADOR = 14
VELOCIDAD_JUGADOR = 5.0

# ==================== ENEMIGOS ====================
VELOCIDAD_PERSEGUIDOR = [1.0, 1.8, 2.5]
VELOCIDAD_INVISIBLE = [0.0, 0.6, 0.9]
ALFA_INVISIBLE = 40
DISTANCIA_SEGURA_SPAWN = 180

# ==================== ILUMINACION ====================
# Nivel 1: sin oscuridad, Nivel 2: luz media, Nivel 3: luz pequena + parpadeo
RADIO_LUZ_NIVEL_2 = 120
RADIO_LUZ_NIVEL_3 = 70
RADIO_LUZ_CEGUERA_NIVEL_1 = 90
DURACION_PARPADEO_LUZ = 0.3
INTERVALO_PARPADEO_MIN = 3000
INTERVALO_PARPADEO_MAX = 5000

# ==================== HABILIDADES ====================
TAM_CAJA = 22
CAJAS_POR_NIVEL = 2
DURACION_INMUNIDAD = 2.0
DURACION_CONGELAMIENTO = 3.0
DURACION_SONAR = 2.5
DURACION_DECOY = 4.0
DECOY_TAM = 20

# ==================== DEBUFFS ====================
DURACION_DEBUFF = 4.0
SLOWDOWN_FACTOR = 0.5
BLINDNESS_FACTOR = 0.5

# Tipos de debuff
DEBUFF_SLOWDOWN = 1
DEBUFF_BLINDNESS = 2
DEBUFF_INVERTED = 3

# ==================== SCREAMER ====================
DURACION_SCR_PEQUENO = 1.8

# ==================== VOLUMEN ====================
VOLUMEN_MUSICA = 0.5
VOLUMEN_SFX = 0.7

# ==================== ESTADOS ====================
MENU = "menu"
OPCIONES = "opciones"
AYUDA = "ayuda"
JUGANDO = "jugando"
TE_ENCONTRARON = "te_encontraron"
SCREAMER = "screamer"
GAME_OVER = "game_over"
VICTORIA = "victoria"

# Matrices de niveles: 1 = pared, 0 = camino
NIVEL_1 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,0,1,1,1,0,1,0,1,0,1],
    [1,0,1,0,0,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,1,0,1],
    [1,1,1,0,1,0,1,1,1,1,1,0,1,0,1],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    [1,0,1,1,1,1,1,1,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,1,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,0,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,0,1,1,1,0,1,1,1,1,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

NIVEL_2 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,1,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
    [1,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,1,1,0,1,1,1,0,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,1,0,1],
    [1,0,1,1,1,0,1,1,1,1,1,0,1,0,1],
    [1,0,1,0,0,0,0,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,1,1,1,1,0,1,1,1,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,1,0,1],
    [1,1,1,0,1,0,1,1,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,0,1,0,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

NIVEL_3 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,0,1,0,0,0,1,0,0,0,0,0,0,1],
    [1,1,0,1,0,1,0,1,0,1,1,1,1,0,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,0,1,1,0,1,1,1,0,1,0,1,1,1,1],
    [1,0,0,1,0,0,0,0,0,0,0,1,0,0,1],
    [1,1,0,1,1,1,0,1,1,1,0,1,0,1,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,0,1,1,0,1,1,1,0,1,1,1,1,0,1],
    [1,0,0,1,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,0,1,0,1,1,1,1,1,1,1,1,0,1],
    [1,0,0,0,0,1,0,0,0,0,0,0,1,0,1],
    [1,0,1,1,1,1,0,1,0,1,1,0,1,0,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

NIVELES = [NIVEL_1, NIVEL_2, NIVEL_3]
