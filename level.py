# -*- coding: utf-8 -*-
"""
level.py - Clase Level para gestionar el laberinto, spawning seguro y mascara de oscuridad.
"""

import pygame
import random
import math
from settings import *
from entities import Perseguidor, Invisible, Trampa


class Level:
    """Representa un nivel del laberinto."""

    def __init__(self, matriz):
        self.matriz = matriz
        self.filas = len(matriz)
        self.columnas = len(matriz[0])
        self.paredes = []
        self.celdas_libres = []
        self.posicion_inicio = None
        self.posicion_salida = None
        self._generar_paredes()
        self._encontrar_celdas_libres()
        self._superficie_mapa = None
        self._pre_renderizar()

    def _generar_paredes(self):
        """Genera los Rect de las paredes."""
        for fila in range(self.filas):
            for col in range(self.columnas):
                if self.matriz[fila][col] == 1:
                    rect = pygame.Rect(col * TAM_CELDA, fila * TAM_CELDA, TAM_CELDA, TAM_CELDA)
                    self.paredes.append(rect)

    def _encontrar_celdas_libres(self):
        """Encuentra celdas libres y establece inicio/salida."""
        for fila in range(self.filas):
            for col in range(self.columnas):
                if self.matriz[fila][col] == 0:
                    x = col * TAM_CELDA + TAM_CELDA // 2
                    y = fila * TAM_CELDA + TAM_CELDA // 2
                    self.celdas_libres.append((x, y, fila, col))

        if self.celdas_libres:
            self.posicion_inicio = (self.celdas_libres[0][0], self.celdas_libres[0][1])
            self.posicion_salida = (self.celdas_libres[-1][0], self.celdas_libres[-1][1])

    def _pre_renderizar(self):
        """Pre-renderiza el laberinto completo."""
        w = self.columnas * TAM_CELDA
        h = self.filas * TAM_CELDA
        self._superficie_mapa = pygame.Surface((w, h))
        self._superficie_mapa.fill(GRIS_CAMINO)

        for pared in self.paredes:
            pygame.draw.rect(self._superficie_mapa, GRIS_PARED, pared)
            pygame.draw.rect(self._superficie_mapa, GRIS_OSCURO, pared, 1)

        if self.posicion_salida:
            sal = pygame.Rect(self.posicion_salida[0] - 8, self.posicion_salida[1] - 8, 16, 16)
            pygame.draw.rect(self._superficie_mapa, VERDE_JUGADOR, sal)
            pygame.draw.rect(self._superficie_mapa, BLANCO, sal, 2)

    def es_pared_xy(self, x, y):
        """Verifica si una posicion en pixeles es pared."""
        col = int(x) // TAM_CELDA
        fil = int(y) // TAM_CELDA
        if 0 <= fil < self.filas and 0 <= col < self.columnas:
            return self.matriz[fil][col] == 1
        return True

    def colision_con_paredes(self, rect):
        """Verifica si un rect colisiona con alguna pared."""
        for pared in self.paredes:
            if rect.colliderect(pared):
                return True
        return False

    def _distancia_a_inicio(self, x, y):
        """Calcula la distancia euclidiana desde una posicion hasta el inicio."""
        if self.posicion_inicio:
            dx = x - self.posicion_inicio[0]
            dy = y - self.posicion_inicio[1]
            return math.sqrt(dx * dx + dy * dy)
        return float('inf')

    def obtener_celdas_libres_para_spawn(self, cantidad, excluir_pos=None):
        """
        Retorna celdas libres aleatorias para spawnear.
        Excluye celdas dentro de DISTANCIA_SEGURA_SPAWN del punto de inicio.
        """
        celdas = []
        for x, y, f, c in self.celdas_libres:
            if (x, y) == excluir_pos:
                continue
            if self._distancia_a_inicio(x, y) < DISTANCIA_SEGURA_SPAWN:
                continue
            celdas.append((x, y))

        random.shuffle(celdas)
        return celdas[:cantidad]

    def dibujar(self, superficie):
        """Dibuja el laberinto pre-renderizado."""
        superficie.blit(self._superficie_mapa, (0, 0))


class LightingMask:
    """Mascara de oscuridad con circulo de luz centrado en el cursor."""

    def __init__(self):
        self.surf_mask = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self.parapadeando = False
        self.tiempo_parpadeo = 0
        self.proximo_parpadeo = 0
        self._activar_proximo_parpadeo()
        # Flicker animation state
        self._flicker_fases = []
        self._flicker_idx = 0
        self._flicker_start = 0
        self._generar_fases_flicker()

    def _generar_fases_flicker(self):
        """Genera secuencia de fases tipo foco descompuesto: rapido on/off."""
        import random
        fases = []
        for _ in range(random.randint(8, 15)):
            duracion = random.randint(30, 120)
            encendido = random.random() > 0.4
            fases.append((duracion, encendido))
        fases.append((200, False))
        self._flicker_fases = fases
        self._flicker_idx = 0
        self._flicker_start = 0

    def _activar_proximo_parpadeo(self):
        self.proximo_parpadeo = pygame.time.get_ticks() + random.randint(
            INTERVALO_PARPADEO_MIN, INTERVALO_PARPADEO_MAX
        )

    def actualizar(self, nivel_indice):
        if nivel_indice != 2:
            return
        t = pygame.time.get_ticks()
        if not self.parapadeando and t >= self.proximo_parpadeo:
            self.parapadeando = True
            self.tiempo_parpadeo = t
            self._flicker_start = t
            self._flicker_idx = 0
            self._generar_fases_flicker()
        elif self.parapadeando:
            total_fases = len(self._flicker_fases)
            if self._flicker_idx < total_fases:
                dur, _ = self._flicker_fases[self._flicker_idx]
                if t - self._flicker_start >= dur:
                    self._flicker_start += dur
                    self._flicker_idx += 1
            else:
                self.parapadeando = False
                self._activar_proximo_parpadeo()

    def dibujar(self, pantalla, nivel_indice, mouse_x, mouse_y, radio_base, debuff_ceguera=False):
        # Nivel 1 sin oscuridad a menos que tenga ceguera
        if nivel_indice == 0 and not debuff_ceguera:
            return

        radio = radio_base
        if debuff_ceguera:
            if nivel_indice == 0:
                radio = RADIO_LUZ_CEGUERA_NIVEL_1
            else:
                radio = int(radio * BLINDNESS_FACTOR)

        encendido = True
        if nivel_indice == 2 and self.parapadeando:
            if self._flicker_idx < len(self._flicker_fases):
                _, encendido = self._flicker_fases[self._flicker_idx]
            else:
                encendido = False

        if nivel_indice == 2 and self.parapadeando and not encendido:
            radio = 0

        alpha = 245 if nivel_indice == 2 else (210 if nivel_indice == 1 else 220)
        if nivel_indice == 2 and self.parapadeando and encendido:
            alpha = max(180, alpha - 40)

        self.surf_mask.fill((0, 0, 0, alpha))

        if radio > 0:
            pygame.draw.circle(self.surf_mask, (0, 0, 0, 0), (mouse_x, mouse_y), radio)

        pantalla.blit(self.surf_mask, (0, 0))


class EnemigosManager:
    """Gestiona la creacion y actualizacion de enemigos por nivel."""

    def __init__(self):
        self.perseguidores = []
        self.invisibles = []
        self.trampas = []

    def crear_enemigos_nivel(self, nivel, jugador_pos):
        """Crea enemigos y trampas respetaiendo zona segura de spawn."""
        self.perseguidores.clear()
        self.invisibles.clear()
        self.trampas.clear()

        num_nivel = NIVELES.index(nivel.matriz) if nivel.matriz in NIVELES else 0

        # Perseguidores: 1 en nivel 1, 2 en nivel 2, 2 en nivel 3
        celdas = nivel.obtener_celdas_libres_para_spawn(1 + min(num_nivel, 1), jugador_pos)
        vel_perseguidor = VELOCIDAD_PERSEGUIDOR[num_nivel]
        for x, y in celdas:
            self.perseguidores.append(Perseguidor(x - (TAM_CELDA - 10) // 2,
                                                   y - (TAM_CELDA - 10) // 2,
                                                   velocidad=vel_perseguidor))

        # Invisibles: 0 en nivel 1, 1 en nivel 2, 1 en nivel 3
        if num_nivel >= 1:
            vel_invisible = VELOCIDAD_INVISIBLE[num_nivel]
            celdas = nivel.obtener_celdas_libres_para_spawn(1, jugador_pos)
            for x, y in celdas:
                self.invisibles.append(Invisible(x - (TAM_CELDA - 10) // 2,
                                                  y - (TAM_CELDA - 10) // 2,
                                                  velocidad=vel_invisible))

        # Trampas: 2 en nivel 1, 3 en nivel 2, 4 en nivel 3
        celdas = nivel.obtener_celdas_libres_para_spawn(2 + num_nivel, jugador_pos)
        for x, y in celdas:
            self.trampas.append(Trampa(x - TAM_CELDA // 2, y - TAM_CELDA // 2))

    def actualizar(self, jugador_pos, nivel, congelar=False, decoy_pos=None):
        """Actualiza todos los enemigos."""
        for p in self.perseguidores:
            p.congelado = congelar
            p.actualizar(jugador_pos, nivel, decoy_pos=decoy_pos)

        for i in self.invisibles:
            i.congelado = congelar
            i.actualizar(jugador_pos, nivel=nivel)

        for t in self.trampas:
            t.actualizar()

    def dibujar(self, superficie):
        """Dibuja todos los enemigos y trampas."""
        for t in self.trampas:
            t.dibujar(superficie)
        for i in self.invisibles:
            i.dibujar(superficie)
        for p in self.perseguidores:
            p.dibujar(superficie)
