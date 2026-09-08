# -*- coding: utf-8 -*-
"""
skills.py - Sistema de habilidades: SkillManager, CajaHabilidad y Decoy.
4 habilidades activadas exclusivamente con clic derecho.
"""

import pygame
import math
import random
from settings import *


class SkillManager:
    """
    Gestiona las 4 habilidades del jugador.
    Todas se activan con clic derecho (event.button == 3).
    Solo se puede tener 1 habilidad equipada a la vez.
    """

    # IDs de habilidad
    HAB_INMUNIDAD = 1
    HAB_CONGELAR = 2
    HAB_SONAR = 3
    HAB_DECOY = 4

    Nombres = {
        1: "INMUNIDAD",
        2: "CONGELAR",
        3: "SONAR",
        4: "DECOY",
    }

    Colores = {
        1: DORADO,
        2: AZUL_INVISIBLE,
        3: CIAN,
        4: NARANJA,
    }

    def __init__(self):
        self.habilidad_actual = None
        # Estados de habilidades activas
        self.inmunidad_activa = False
        self.congelamiento_activo = False
        self.sonar_activo = False
        self.decoy_activo = False
        # Tiempos de activacion
        self.tiempo_inmunidad = 0
        self.tiempo_congelamiento = 0
        self.tiempo_sonar = 0
        self.tiempo_decoy = 0
        # Posicion del decoy (se activa con clic derecho)
        self.decoy_pos = None
        # Mensaje informativo
        self.mensaje = ""
        self.tiempo_mensaje = 0

    def equipar_aleatoria(self):
        """Equipa una habilidad aleatoria al tocar una caja."""
        self.habilidad_actual = random.choice([
            self.HAB_INMUNIDAD,
            self.HAB_CONGELAR,
            self.HAB_SONAR,
            self.HAB_DECOY,
        ])
        nombre = self.Nombres[self.habilidad_actual]
        self.mensaje = f"+ {nombre} [CLK IZQ]"
        self.tiempo_mensaje = pygame.time.get_ticks()

    def usar_habilidad(self, boton_raton, mouse_pos=None):
        """
        Usa la habilidad equipada al presionar clic derecho.
        Retorna el tipo de habilidad usada o None.
        """
        if boton_raton != 1 or self.habilidad_actual is None:
            return None

        hab = self.habilidad_actual
        self.habilidad_actual = None
        t = pygame.time.get_ticks()

        if hab == self.HAB_INMUNIDAD:
            self.inmunidad_activa = True
            self.tiempo_inmunidad = t
            return hab

        elif hab == self.HAB_CONGELAR:
            self.congelamiento_activo = True
            self.tiempo_congelamiento = t
            return hab

        elif hab == self.HAB_SONAR:
            self.sonar_activo = True
            self.tiempo_sonar = t
            return hab

        elif hab == self.HAB_DECOY:
            if mouse_pos:
                self.decoy_activo = True
                self.tiempo_decoy = t
                self.decoy_pos = mouse_pos
                return hab

        return None

    def actualizar(self):
        """Actualiza duracion de todas las habilidades activas."""
        t = pygame.time.get_ticks()

        if self.inmunidad_activa and t - self.tiempo_inmunidad >= int(DURACION_INMUNIDAD * 1000):
            self.inmunidad_activa = False

        if self.congelamiento_activo and t - self.tiempo_congelamiento >= int(DURACION_CONGELAMIENTO * 1000):
            self.congelamiento_activo = False

        if self.sonar_activo and t - self.tiempo_sonar >= int(DURACION_SONAR * 1000):
            self.sonar_activo = False

        if self.decoy_activo and t - self.tiempo_decoy >= int(DURACION_DECOY * 1000):
            self.decoy_activo = False
            self.decoy_pos = None

        if self.mensaje and t - self.tiempo_mensaje >= 2500:
            self.mensaje = ""

    def resetear_habilidades_activas(self):
        """Resetea todas las habilidades activas (al morir/reiniciar)."""
        self.inmunidad_activa = False
        self.congelamiento_activo = False
        self.sonar_activo = False
        self.decoy_activo = False
        self.decoy_pos = None

    def dibujar_hud(self, superficie):
        """Dibuja indicadores de habilidades en pantalla."""
        fuente = pygame.font.SysFont(None, 26)

        # Habilidad equipada
        if self.habilidad_actual:
            nombre = self.Nombres[self.habilidad_actual]
            color = self.Colores[self.habilidad_actual]
            txt = f"HABILIDAD: {nombre} [CLK IZQ]"
            s = fuente.render(txt, True, color)
            superficie.blit(s, (ANCHO - s.get_width() - 15, 50))

        # Indicadores de habilidades activas
        y_indicador = ALTO - 60
        if self.inmunidad_activa:
            s = fuente.render("INMUNIDAD ACTIVA", True, DORADO)
            superficie.blit(s, (15, y_indicador))
            y_indicador -= 25

        if self.congelamiento_activo:
            s = fuente.render("ENEMIGOS CONGELADOS", True, AZUL_INVISIBLE)
            superficie.blit(s, (15, y_indicador))
            y_indicador -= 25

        if self.sonar_activo:
            s = fuente.render("SONAR ACTIVO", True, CIAN)
            superficie.blit(s, (15, y_indicador))
            y_indicador -= 25

        if self.decoy_activo:
            s = fuente.render("DECOY ACTIVO", True, NARANJA)
            superficie.blit(s, (15, y_indicador))
            y_indicador -= 25

        # Mensaje de habilidad recogida
        if self.mensaje:
            s = fuente.render(self.mensaje, True, AMARILLO)
            superficie.blit(s, (ANCHO // 2 - s.get_width() // 2, ALTO // 2 + 60))


class Decoy:
    """Entidad estatica que atrae enemigos durante un tiempo limitado."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x - DECOY_TAM // 2, y - DECOY_TAM // 2, DECOY_TAM, DECOY_TAM)
        self.pos = (x, y)
        self.tiempo_creado = pygame.time.get_ticks()

    def dibujar(self, superficie):
        """Dibuja el decoy como un cuadrado naranja pulsante con anillo."""
        t = pygame.time.get_ticks()
        pulso = int(180 + 75 * math.sin(t * 0.008))
        color = (NARANJA[0], min(255, pulso), 0)
        pygame.draw.rect(superficie, color, self.rect)
        pygame.draw.rect(superficie, BLANCO, self.rect, 2)
        radio = int(30 + 10 * math.sin(t * 0.006))
        pygame.draw.circle(superficie, NARANJA, self.rect.center, radio, 2)


class CajaHabilidad:
    """Caja que otorga una habilidad aleatoria al ser tocada."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x - TAM_CAJA // 2, y - TAM_CAJA // 2, TAM_CAJA, TAM_CAJA)
        self.activa = True

    def verificar_colision(self, jugador_rect):
        """Retorna True si el jugador toca la caja."""
        if self.activa and self.rect.colliderect(jugador_rect):
            self.activa = False
            return True
        return False

    def dibujar(self, superficie):
        """Dibuja la caja dorada pulsante."""
        if self.activa:
            t = pygame.time.get_ticks()
            brillo = int(180 + 75 * math.sin(t * 0.005))
            color = (brillo, min(255, brillo + 30), 0)
            pygame.draw.rect(superficie, color, self.rect)
            pygame.draw.rect(superficie, BLANCO, self.rect, 2)
            fuente = pygame.font.SysFont(None, 16)
            s = fuente.render("?", True, NEGRO)
            superficie.blit(s, s.get_rect(center=self.rect.center))
