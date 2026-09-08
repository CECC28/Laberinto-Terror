# -*- coding: utf-8 -*-
"""
entities.py - Entidades del juego: Jugador, Enemigos, Trampas, Screamer.
Sistema de debuffs y colision predictiva para enemigos.
"""

import pygame
import math
import random

try:
    import cv2
    CV2_DISPONIBLE = True
except ImportError:
    CV2_DISPONIBLE = False

from settings import *


class Jugador:
    """Representa al jugador, un cuadrado verde que sigue al cursor."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TAM_JUGADOR, TAM_JUGADOR)
        self.vidas = VIDAS
        self.pos_inicial = (x, y)
        self.inmunidad = False
        self.vivo = True
        # Superficies pre-renderizadas
        self._sup_normal = pygame.Surface((TAM_JUGADOR, TAM_JUGADOR), pygame.SRCALPHA)
        pygame.draw.rect(self._sup_normal, VERDE_JUGADOR, (0, 0, TAM_JUGADOR, TAM_JUGADOR))
        pygame.draw.rect(self._sup_normal, BLANCO, (0, 0, TAM_JUGADOR, TAM_JUGADOR), 2)
        self._sup_inmune = pygame.Surface((TAM_JUGADOR, TAM_JUGADOR), pygame.SRCALPHA)
        pygame.draw.rect(self._sup_inmune, DORADO, (0, 0, TAM_JUGADOR, TAM_JUGADOR))
        pygame.draw.rect(self._sup_inmune, BLANCO, (0, 0, TAM_JUGADOR, TAM_JUGADOR), 2)

        # Debuffs activos: {tipo: tiempo_fin}
        self.debuffs = {}
        self.control_invertido = False
        self._inversion_origen = None  # Posicion del jugador al activar invertido
        # Proteccion post-danio (0.5s de inmunidad al recibir hit)
        self._proteccion_danio = False
        self._tiempo_proteccion = 0

    def actualizar(self, nivel=None):
        """Mueve el jugador hacia la posicion del cursor con lerp (suavizado)."""
        if not self.vivo:
            return

        mx, my = pygame.mouse.get_pos()

        # Calcular delta hacia el cursor
        if self.control_invertido and self._inversion_origen:
            # Inversion relativa a donde estaba el jugador al activarse
            ox, oy = self._inversion_origen
            dx = -(mx - ox)
            dy = -(my - oy)
        else:
            dx = mx - self.rect.centerx
            dy = my - self.rect.centery

        # Factor de interpolacion (0.12 = normal, 0.04 = ralentizado)
        lerp = 0.12
        if DEBUFF_SLOWDOWN in self.debuffs:
            lerp = 0.04

        nuevo_x = self.rect.centerx + dx * lerp
        nuevo_y = self.rect.centery + dy * lerp

        # Cap de velocidad para no saltar paredes
        max_move = TAM_CELDA // 4
        nuevo_x = max(self.rect.centerx - max_move, min(nuevo_x, self.rect.centerx + max_move))
        nuevo_y = max(self.rect.centery - max_move, min(nuevo_y, self.rect.centery + max_move))

        # Verificar colision con paredes ANTES de mover
        if nivel is not None:
            test_rect_x = pygame.Rect(nuevo_x - self.rect.width // 2,
                                       self.rect.y, self.rect.width, self.rect.height)
            test_rect_y = pygame.Rect(self.rect.x,
                                       nuevo_y - self.rect.height // 2, self.rect.width, self.rect.height)

            if not nivel.colision_con_paredes(test_rect_x):
                self.rect.centerx = nuevo_x
            if not nivel.colision_con_paredes(test_rect_y):
                self.rect.centery = nuevo_y
        else:
            self.rect.centerx = nuevo_x
            self.rect.centery = nuevo_y

    def aplicar_debuff(self, tipo):
        """Aplica un debuff al jugador durante DURACION_DEBUFF segundos."""
        self.debuffs[tipo] = pygame.time.get_ticks() + int(DURACION_DEBUFF * 1000)
        if tipo == DEBUFF_INVERTED:
            self.control_invertido = True
            self._inversion_origen = (self.rect.centerx, self.rect.centery)

    def actualizar_debuffs(self):
        """Actualiza y elimina debuffs expirados."""
        t = pygame.time.get_ticks()
        # Limpiar proteccion post-danio despues de 0.5s
        if self._proteccion_danio and t - self._tiempo_proteccion >= 500:
            self._proteccion_danio = False
        expirados = [tipo for tipo, fin in self.debuffs.items() if t >= fin]
        for tipo in expirados:
            del self.debuffs[tipo]
            if tipo == DEBUFF_INVERTED:
                self.control_invertido = False
                self._inversion_origen = None

    def tiene_debuff(self, tipo):
        """Verifica si un debuff esta activo."""
        return tipo in self.debuffs

    def recibir_danio(self):
        """Resta una vida si no tiene inmunidad/proteccion. Retorna (vidas, hubo_danio)."""
        if not self.inmunidad and not self._proteccion_danio:
            self.vidas -= 1
            self._proteccion_danio = True
            self._tiempo_proteccion = pygame.time.get_ticks()
            if self.vidas <= 0:
                self.vivo = False
            return self.vidas, True
        return self.vidas, False

    def dibujar(self, superficie):
        """Dibuja al jugador."""
        if self.inmunidad:
            superficie.blit(self._sup_inmune, self.rect.topleft)
        else:
            superficie.blit(self._sup_normal, self.rect.topleft)


class Perseguidor:
    """Enemigo que se mueve hacia el jugador o hacia un decoy."""

    def __init__(self, x, y, velocidad=1.0):
        self.rect = pygame.Rect(x, y, TAM_CELDA - 10, TAM_CELDA - 10)
        self.velocidad = velocidad
        self.congelado = False
        # Superficies pre-renderizadas
        self._sup_normal = pygame.Surface((self.rect.width, self.rect.height))
        self._sup_normal.fill(ROJO)
        pygame.draw.rect(self._sup_normal, ROJO_OSCURO, (0, 0, self.rect.width, self.rect.height), 2)
        self._sup_congelado = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(self._sup_congelado, (50, 120, 255, 200), (0, 0, self.rect.width, self.rect.height))
        pygame.draw.rect(self._sup_congelado, BLANCO, (0, 0, self.rect.width, self.rect.height), 2)

    def _es_posicion_valida(self, x, y, nivel):
        """Verifica si las 4 esquinas de una posicion estan libres de paredes."""
        w = self.rect.width
        h = self.rect.height
        esquinas = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
        for ex, ey in esquinas:
            if nivel.es_pared_xy(ex, ey):
                return False
        return True

    def actualizar(self, jugador_pos, nivel, decoy_pos=None):
        """Mueve al perseguidor hacia el jugador o decoy."""
        if self.congelado:
            return

        # Si hay decoy activo, ir hacia el decoy en lugar del jugador
        objetivo = decoy_pos if decoy_pos else jugador_pos

        dx = objetivo[0] - self.rect.centerx
        dy = objetivo[1] - self.rect.centery
        dist_sq = dx * dx + dy * dy

        if dist_sq > 1:
            inv = 1.0 / math.sqrt(dist_sq)
            mx = dx * inv * self.velocidad
            my = dy * inv * self.velocidad

            # Intentar mover en X con colision predictiva de 4 esquinas
            nueva_x = self.rect.x + mx
            if self._es_posicion_valida(nueva_x, self.rect.y, nivel):
                self.rect.x = nueva_x

            # Intentar mover en Y con colision predictiva de 4 esquinas
            nueva_y = self.rect.y + my
            if self._es_posicion_valida(self.rect.x, nueva_y, nivel):
                self.rect.y = nueva_y

    def congelar(self):
        self.congelado = True

    def dibujar(self, superficie):
        if self.congelado:
            superficie.blit(self._sup_congelado, self.rect.topleft)
        else:
            superficie.blit(self._sup_normal, self.rect.topleft)


class Invisible:
    """Enemigo casi transparente que se acerca al jugador silenciosamente."""

    def __init__(self, x, y, velocidad=0.5):
        self.rect = pygame.Rect(x, y, TAM_CELDA - 10, TAM_CELDA - 10)
        self.alfa = ALFA_INVISIBLE
        self.congelado = False
        self.volumen = 0.0
        self.velocidad = velocidad

    def actualizar(self, jugador_pos, nivel=None):
        """Mueve al invisible hacia el jugador."""
        if self.congelado:
            return
        dx = jugador_pos[0] - self.rect.centerx
        dy = jugador_pos[1] - self.rect.centery
        dist = math.sqrt(dx * dx + dy * dy)
        max_dist = TAM_CELDA * 7
        if dist < max_dist:
            self.volumen = 1.0 - (dist / max_dist) * 0.95
        else:
            self.volumen = 0.05
        if dist > 1 and nivel is not None:
            inv = 1.0 / dist
            nueva_x = self.rect.x + dx * inv * self.velocidad
            nueva_y = self.rect.y + dy * inv * self.velocidad
            w = self.rect.width
            h = self.rect.height
            esq_ok_x = True
            esq_ok_y = True
            for ex, ey in [(nueva_x, self.rect.y), (nueva_x + w, self.rect.y),
                           (nueva_x, self.rect.y + h), (nueva_x + w, self.rect.y + h)]:
                if nivel.es_pared_xy(ex, ey):
                    esq_ok_x = False
                    break
            for ex, ey in [(self.rect.x, nueva_y), (self.rect.x + w, nueva_y),
                           (self.rect.x, nueva_y + h), (self.rect.x + w, nueva_y + h)]:
                if nivel.es_pared_xy(ex, ey):
                    esq_ok_y = False
                    break
            if esq_ok_x:
                self.rect.x = nueva_x
            if esq_ok_y:
                self.rect.y = nueva_y

    def congelar(self):
        self.congelado = True

    def dibujar(self, superficie):
        sup = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        color = (AZUL_INVISIBLE[0], AZUL_INVISIBLE[1], AZUL_INVISIBLE[2], self.alfa)
        pygame.draw.rect(sup, color, (0, 0, self.rect.width, self.rect.height))
        pygame.draw.rect(sup, (200, 200, 255, self.alfa + 30), (0, 0, self.rect.width, self.rect.height), 2)
        superficie.blit(sup, self.rect.topleft)


class Trampa:
    """
    Trampa que NO quita vida. Aplica un debuff aleatorio al contacto.
    Tipos: Ralentizacion, Ceguera, Controles invertidos.
    """

    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 6, y + 6, TAM_CELDA - 12, TAM_CELDA - 12)
        self.activa = True
        self.alpha = 0
        self.tiempo_aparicion = pygame.time.get_ticks()
        # Tipo de debuff que aplica esta trampa
        self.tipo_debuff = random.choice([DEBUFF_SLOWDOWN, DEBUFF_BLINDNESS, DEBUFF_INVERTED])

    def verificar_colision(self, jugador_rect):
        """Verifica si el jugador toca la trampa. Retorna el tipo de debuff o None."""
        if self.activa and self.rect.colliderect(jugador_rect):
            self.activa = False
            return self.tipo_debuff
        return None

    def actualizar(self):
        """Aparece gradualmente."""
        t = pygame.time.get_ticks() - self.tiempo_aparicion
        if t < 400:
            self.alpha = int((t / 400) * 255)
        else:
            self.alpha = 255

    def dibujar(self, superficie):
        """Dibuja la trampa con un color uniforme que no revela su debuff."""
        if self.activa and self.alpha > 0:
            sup = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            c = (70, 30, 90, self.alpha)
            pygame.draw.rect(sup, c, (0, 0, self.rect.width, self.rect.height))
            pygame.draw.rect(sup, (255, 255, 255, self.alpha), (0, 0, self.rect.width, self.rect.height), 2)
            superficie.blit(sup, self.rect.topleft)


class ScreamerManager:
    """Maneja los screamers y la foto de webcam."""

    def __init__(self):
        self.activo = False
        self.tiempo_inicio = 0
        self.duracion = 0
        self._superficie = None
        self._foto_surface = None

    def activar_screamer_pequeno(self):
        """Activa pantalla 'TE ENCONTRARON'."""
        self.activo = True
        self.tiempo_inicio = pygame.time.get_ticks()
        self.duracion = int(DURACION_SCR_PEQUENO * 1000)
        self._superficie = pygame.Surface((ANCHO, ALTO))
        self._superficie.fill(ROJO)
        fuente = pygame.font.SysFont(None, 72)
        texto = fuente.render("TE ENCONTRARON!", True, BLANCO)
        r = texto.get_rect(center=(ANCHO // 2, ALTO // 2))
        self._superficie.blit(texto, r)

    def activar_screamer_grande(self):
        """Activa game over y toma foto."""
        self.activo = True
        self.tiempo_inicio = pygame.time.get_ticks()
        self.duracion = 2500
        self._tomar_foto_webcam()
        self._superficie = pygame.Surface((ANCHO, ALTO))
        self._superficie.fill(NEGRO)
        fuente = pygame.font.SysFont(None, 100)
        texto = fuente.render("GAME OVER", True, ROJO)
        r = texto.get_rect(center=(ANCHO // 2, 60))
        self._superficie.blit(texto, r)
        if self._foto_surface:
            self._superficie.blit(self._foto_surface, (ANCHO // 2 - 160, ALTO // 2 - 120))
            borde = pygame.Rect(ANCHO // 2 - 162, ALTO // 2 - 122, 324, 244)
            pygame.draw.rect(self._superficie, BLANCO, borde, 2)
            fuente_sm = pygame.font.SysFont(None, 24)
            txt_foto = fuente_sm.render("Foto guardada: foto_webcam.jpg", True, GRIS_CAMINO)
            self._superficie.blit(txt_foto, txt_foto.get_rect(center=(ANCHO // 2, ALTO // 2 + 135)))
        else:
            fuente_sm = pygame.font.SysFont(None, 30)
            txt_no = fuente_sm.render("Sin camara disponible", True, GRIS_CAMINO)
            self._superficie.blit(txt_no, txt_no.get_rect(center=(ANCHO // 2, ALTO // 2)))
        fuente_ck = pygame.font.SysFont(None, 28)
        txt_ck = fuente_ck.render("CLICK PARA REINICIAR", True, BLANCO)
        self._superficie.blit(txt_ck, txt_ck.get_rect(center=(ANCHO // 2, ALTO - 60)))

    def _tomar_foto_webcam(self):
        self._foto_surface = None
        if CV2_DISPONIBLE:
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        cv2.imwrite("foto_webcam.jpg", frame)
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w = frame_rgb.shape[:2]
                        escala = min(320 / w, 240 / h)
                        nuevo_w = int(w * escala)
                        nuevo_h = int(h * escala)
                        surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                        surf = pygame.transform.smoothscale(surf, (nuevo_w, nuevo_h))
                        self._foto_surface = surf
                    cap.release()
            except Exception:
                pass

    def actualizar(self):
        if self.activo:
            if pygame.time.get_ticks() - self.tiempo_inicio >= self.duracion:
                self.activo = False

    def dibujar(self, superficie):
        if self.activo and self._superficie:
            superficie.blit(self._superficie, (0, 0))
