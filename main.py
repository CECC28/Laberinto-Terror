# -*- coding: utf-8 -*-
"""
main.py - Archivo principal: game loop, estados, camara, iluminacion, debuffs.
"""

import pygame
import sys
import math
from settings import *
from level import Level, EnemigosManager, LightingMask
from entities import Jugador, ScreamerManager
from skills import SkillManager, CajaHabilidad, Decoy


# Radio de luz por nivel (indice 0 = nivel 1, indice 1 = nivel 2, indice 2 = nivel 3)
RADIOS_LUZ = [0, RADIO_LUZ_NIVEL_2, RADIO_LUZ_NIVEL_3]


class Game:
    """Clase principal que gestiona todo el juego."""

    def __init__(self):
        pygame.init()
        self.pantalla_completa = False
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption(TITULO)
        self.reloj = pygame.time.Clock()
        pygame.mouse.set_visible(True)

        # Estado
        self.estado = MENU
        self.nivel_actual = 0
        self.level = None
        self.jugador = None
        self.enemigos_manager = None
        self.skill_manager = SkillManager()
        self.screamer_manager = ScreamerManager()
        self.cajas = []
        self.decoy = None

        # Iluminacion
        self.lighting = LightingMask()

        # Camara
        self.camera_x = 0
        self.camera_y = 0

        # TE ENCONTRARON
        self.tiempo_te_encontraron = 0
        self.duracion_te_encontraron = 1500

        # Superficie de juego
        self.superficie_juego = pygame.Surface((ANCHO, ALTO))

        # Volumen
        self.volumen_musica = VOLUMEN_MUSICA
        self.volumen_sfx = VOLUMEN_SFX

        # Fuentes
        self.fuente_huge = pygame.font.SysFont(None, 80)
        self.fuente_grande = pygame.font.SysFont(None, 56)
        self.fuente_mediana = pygame.font.SysFont(None, 36)
        self.fuente_pequena = pygame.font.SysFont(None, 26)
        self.fuente_tiny = pygame.font.SysFont(None, 20)

        # Imagen de fondo del menu
        self._menu_bg = None
        try:
            self._menu_bg = pygame.image.load("menu_bg.jpg").convert()
            self._menu_bg = pygame.transform.scale(self._menu_bg, (ANCHO, ALTO))
        except Exception:
            pass

        self._pre_renderizar_pantallas()

    def _pre_renderizar_pantallas(self):
        """Pre-renderiza pantallas estaticas."""
        self._sup_te_encontraron = pygame.Surface((ANCHO, ALTO))
        self._sup_te_encontraron.fill(ROJO)
        t1 = self.fuente_huge.render("TE ENCONTRARON!", True, BLANCO)
        self._sup_te_encontraron.blit(t1, t1.get_rect(center=(ANCHO // 2, ALTO // 2)))

        self._sup_game_over = pygame.Surface((ANCHO, ALTO))
        self._sup_game_over.fill(NEGRO)
        t2 = self.fuente_huge.render("GAME OVER", True, ROJO)
        self._sup_game_over.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 3)))
        t3 = self.fuente_mediana.render("Foto guardada: foto_webcam.jpg", True, GRIS_CAMINO)
        self._sup_game_over.blit(t3, t3.get_rect(center=(ANCHO // 2, ALTO // 2)))
        t4 = self.fuente_mediana.render("CLICK PARA REINICIAR", True, BLANCO)
        self._sup_game_over.blit(t4, t4.get_rect(center=(ANCHO // 2, ALTO * 2 // 3)))

        self._sup_victoria = pygame.Surface((ANCHO, ALTO))
        self._sup_victoria.fill(NEGRO)
        tv1 = self.fuente_huge.render("VICTORIA!", True, DORADO)
        self._sup_victoria.blit(tv1, tv1.get_rect(center=(ANCHO // 2, ALTO // 3)))
        tv2 = self.fuente_mediana.render("Has sobrevivido al laberinto", True, BLANCO)
        self._sup_victoria.blit(tv2, tv2.get_rect(center=(ANCHO // 2, ALTO // 2)))
        tv3 = self.fuente_mediana.render("CLICK PARA REINICIAR", True, BLANCO)
        self._sup_victoria.blit(tv3, tv3.get_rect(center=(ANCHO // 2, ALTO * 2 // 3)))

    def toggle_pantalla_completa(self):
        self.pantalla_completa = not self.pantalla_completa
        if self.pantalla_completa:
            self.pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.FULLSCREEN)
        else:
            self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.mouse.set_visible(self.estado not in (JUGANDO, SCREAMER, TE_ENCONTRARON))

    def cargar_nivel(self, indice):
        """Carga un nivel por su indice."""
        if indice >= len(NIVELES):
            self.estado = VICTORIA
            return

        self.nivel_actual = indice
        self.level = Level(NIVELES[indice])

        if self.level.posicion_inicio:
            self.jugador = Jugador(self.level.posicion_inicio[0], self.level.posicion_inicio[1])
        else:
            self.jugador = Jugador(60, 60)

        pygame.mouse.set_pos(self.jugador.rect.center)

        self.enemigos_manager = EnemigosManager()
        self.enemigos_manager.crear_enemigos_nivel(self.level, self.jugador.rect.center)

        self.cajas.clear()
        celdas = self.level.obtener_celdas_libres_para_spawn(CAJAS_POR_NIVEL, self.jugador.rect.center)
        for x, y in celdas:
            self.cajas.append(CajaHabilidad(x, y))

        self.skill_manager = SkillManager()
        self.decoy = None
        self.lighting = LightingMask()

    def reiniciar_nivel(self):
        """Reposiciona jugador, enemigos y limpia estado."""
        if self.level.posicion_inicio:
            self.jugador.rect.centerx = self.level.posicion_inicio[0]
            self.jugador.rect.centery = self.level.posicion_inicio[1]
            pygame.mouse.set_pos(self.jugador.rect.center)
        self.jugador.debuffs.clear()
        self.jugador.control_invertido = False
        self.jugador._inversion_origen = None
        self.jugador.inmunidad = False
        self.jugador._proteccion_danio = False
        self.enemigos_manager.crear_enemigos_nivel(self.level, self.jugador.rect.center)
        self.decoy = None
        self.skill_manager.resetear_habilidades_activas()

    def _procesar_danio(self):
        """Procesa cuando el jugador recibe dano de pared/enemigo/trampa."""
        vidas, hubo_danio = self.jugador.recibir_danio()
        if not hubo_danio:
            return
        if vidas > 0:
            self.estado = TE_ENCONTRARON
            self.tiempo_te_encontraron = pygame.time.get_ticks()
        else:
            self.screamer_manager.activar_screamer_grande()
            self.estado = SCREAMER

    def manejar_eventos(self):
        """Procesa todos los eventos."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.estado in (OPCIONES, AYUDA):
                        self.estado = MENU
                    else:
                        pygame.quit()
                        sys.exit()
                if ev.key == pygame.K_F11:
                    self.toggle_pantalla_completa()

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = pygame.mouse.get_pos()

                if self.estado == MENU:
                    if self._btn_rect("EMPEZAR").collidepoint(mx, my):
                        self.cargar_nivel(0)
                        self.estado = JUGANDO
                        pygame.mouse.set_visible(False)
                    elif self._btn_rect("OPCIONES").collidepoint(mx, my):
                        self.estado = OPCIONES
                    elif self._btn_rect("AYUDA").collidepoint(mx, my):
                        self.estado = AYUDA

                elif self.estado == OPCIONES:
                    if self._btn_rect("VOLUMEN: SUBIR").collidepoint(mx, my):
                        self.volumen_musica = min(1.0, self.volumen_musica + 0.1)
                        self.volumen_sfx = min(1.0, self.volumen_sfx + 0.1)
                    elif self._btn_rect("VOLUMEN: BAJAR").collidepoint(mx, my):
                        self.volumen_musica = max(0.0, self.volumen_musica - 0.1)
                        self.volumen_sfx = max(0.0, self.volumen_sfx - 0.1)
                    elif self._btn_rect("PANTALLA COMPLETA").collidepoint(mx, my):
                        self.toggle_pantalla_completa()
                    elif self._btn_rect("VOLVER").collidepoint(mx, my):
                        self.estado = MENU

                elif self.estado == AYUDA:
                    if self._btn_rect("VOLVER").collidepoint(mx, my):
                        self.estado = MENU

                elif self.estado == JUGANDO and ev.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    world_x = mouse_pos[0] - self.camera_x
                    world_y = mouse_pos[1] - self.camera_y
                    hab = self.skill_manager.usar_habilidad(ev.button, (world_x, world_y))
                    if hab == SkillManager.HAB_INMUNIDAD:
                        self.jugador.inmunidad = True
                    elif hab == SkillManager.HAB_DECOY:
                        self.decoy = Decoy(world_x, world_y)

                elif self.estado in (GAME_OVER, VICTORIA):
                    self.estado = MENU
                    pygame.mouse.set_visible(True)

    def actualizar(self):
        """Actualiza la logica del juego."""
        if self.estado in (MENU, OPCIONES, AYUDA):
            return

        if self.estado == TE_ENCONTRARON:
            if pygame.time.get_ticks() - self.tiempo_te_encontraron >= self.duracion_te_encontraron:
                self.reiniciar_nivel()
                self.estado = JUGANDO
            return

        if self.estado == SCREAMER:
            self.screamer_manager.actualizar()
            if not self.screamer_manager.activo:
                self.estado = GAME_OVER
            return

        if self.estado != JUGANDO:
            return

        # --- JUGANDO ---

        # Actualizar jugador y debuffs
        self.jugador.actualizar(self.level)
        self.jugador.actualizar_debuffs()
        self.skill_manager.actualizar()

        # Sync inmunidad
        self.jugador.inmunidad = self.skill_manager.inmunidad_activa

        # Actualizar iluminacion
        self.lighting.actualizar(self.nivel_actual)

        # Verificar salida PRIMERO
        if self.level.posicion_salida:
            dx = self.jugador.rect.centerx - self.level.posicion_salida[0]
            dy = self.jugador.rect.centery - self.level.posicion_salida[1]
            if dx * dx + dy * dy < (TAM_CELDA // 2) ** 2:
                self.nivel_actual += 1
                if self.nivel_actual >= len(NIVELES):
                    self.estado = VICTORIA
                else:
                    self.cargar_nivel(self.nivel_actual)
                return

        # Colision con paredes (si no tiene inmunidad)
        if not self.jugador.inmunidad and self.level.colision_con_paredes(self.jugador.rect):
            self._procesar_danio()
            return

        # Actualizar enemigos (pasar posicion del decoy si existe)
        decoy_pos = self.decoy.pos if self.decoy else None
        self.enemigos_manager.actualizar(
            self.jugador.rect.center,
            self.level,
            congelar=self.skill_manager.congelamiento_activo,
            decoy_pos=decoy_pos
        )

        # Colision con perseguidores
        if not self.jugador.inmunidad:
            for p in self.enemigos_manager.perseguidores:
                if self.jugador.rect.colliderect(p.rect):
                    self._procesar_danio()
                    return

        # Colision con invisibles
        if not self.jugador.inmunidad:
            for i in self.enemigos_manager.invisibles:
                if self.jugador.rect.colliderect(i.rect):
                    self._procesar_danio()
                    return

        # Colision con trampas (solo aplican debuff, NO quitan vida)
        for t in self.enemigos_manager.trampas:
            debuff_tipo = t.verificar_colision(self.jugador.rect)
            if debuff_tipo is not None:
                self.jugador.aplicar_debuff(debuff_tipo)

        # Colision con cajas de habilidad
        for caja in self.cajas:
            if caja.verificar_colision(self.jugador.rect):
                self.skill_manager.equipar_aleatoria()

    def _btn_rect(self, texto):
        """Retorna el Rect de un boton por su texto."""
        return self._botones.get(texto, pygame.Rect(0, 0, 0, 0))

    def _dibujar_boton(self, texto, cx, cy, ancho=280, alto=52):
        """Dibuja un boton con hover y retorna su rect."""
        mx, my = pygame.mouse.get_pos()
        rect = pygame.Rect(cx - ancho // 2, cy - alto // 2, ancho, alto)
        hover = rect.collidepoint(mx, my)
        color_base = (140, 30, 30) if hover else (90, 20, 20)
        color_borde = ROJO if hover else (160, 40, 40)
        pygame.draw.rect(self.pantalla, color_base, rect, border_radius=6)
        pygame.draw.rect(self.pantalla, color_borde, rect, 3, border_radius=6)
        txt = self.fuente_mediana.render(texto, True, BLANCO)
        self.pantalla.blit(txt, txt.get_rect(center=rect.center))
        return rect

    def dibujar(self):
        """Dibuja todo segun el estado."""
        self.pantalla.fill(NEGRO)
        self._botones = {}

        if self.estado == MENU:
            self._dibujar_menu()
        elif self.estado == OPCIONES:
            self._dibujar_opciones()
        elif self.estado == AYUDA:
            self._dibujar_ayuda()
        elif self.estado == TE_ENCONTRARON:
            self.pantalla.blit(self._sup_te_encontraron, (0, 0))
        elif self.estado == JUGANDO:
            self._dibujar_juego()
        elif self.estado == SCREAMER:
            self._dibujar_juego()
            self.screamer_manager.dibujar(self.pantalla)
        elif self.estado == GAME_OVER:
            if self.screamer_manager._superficie:
                self.pantalla.blit(self.screamer_manager._superficie, (0, 0))
            else:
                self.pantalla.blit(self._sup_game_over, (0, 0))
        elif self.estado == VICTORIA:
            self.pantalla.blit(self._sup_victoria, (0, 0))

        pygame.display.flip()

    def _dibujar_menu(self):
        """Menu principal con imagen de fondo y 3 botones."""
        if self._menu_bg:
            self.pantalla.blit(self._menu_bg, (0, 0))
        else:
            self.pantalla.fill((15, 5, 5))

        self._botones["EMPEZAR"] = self._dibujar_boton("EMPEZAR", ANCHO // 2, ALTO // 2 - 10)
        self._botones["OPCIONES"] = self._dibujar_boton("OPCIONES", ANCHO // 2, ALTO // 2 + 55)
        self._botones["AYUDA"] = self._dibujar_boton("AYUDA", ANCHO // 2, ALTO // 2 + 120)

    def _dibujar_opciones(self):
        """Pantalla de opciones: volumen, pantalla completa."""
        if self._menu_bg:
            self.pantalla.blit(self._menu_bg, (0, 0))
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.pantalla.blit(overlay, (0, 0))

        t = self.fuente_grande.render("OPCIONES", True, ROJO)
        self.pantalla.blit(t, t.get_rect(center=(ANCHO // 2, 60)))

        vol_mus = f"Musica: {int(self.volumen_musica * 100)}%"
        vol_sfx = f"Efectos: {int(self.volumen_sfx * 100)}%"
        self._botones["VOLUMEN: SUBIR"] = self._dibujar_boton(vol_mus + " +", ANCHO // 2, 160, 320, 48)
        self._botones["VOLUMEN: BAJAR"] = self._dibujar_boton(vol_mus + " -", ANCHO // 2, 225, 320, 48)

        fs_txt = "Pantalla Completa (F11)"
        self._botones["PANTALLA COMPLETA"] = self._dibujar_boton(fs_txt, ANCHO // 2, 300, 320, 48)

        self._botones["VOLVER"] = self._dibujar_boton("VOLVER", ANCHO // 2, 400, 200, 48)

    def _dibujar_ayuda(self):
        """Pantalla de ayuda con toda la informacion del juego."""
        if self._menu_bg:
            self.pantalla.blit(self._menu_bg, (0, 0))
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.pantalla.blit(overlay, (0, 0))

        t = self.fuente_grande.render("AYUDA", True, ROJO)
        self.pantalla.blit(t, t.get_rect(center=(ANCHO // 2, 30)))

        y = 65
        controles = [
            "CONTROLES:",
            "Movimiento: Raton (cursor invisible)",
            "F11: Pantalla completa | ESC: Salir",
            "Clic Izquierdo: Usar habilidad equipada",
        ]
        for l in controles:
            txt = self.fuente_pequena.render(l, True, AMARILLO)
            self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
            y += 22

        y += 8
        txt = self.fuente_pequena.render("OBJETOS:", True, DORADO)
        self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
        y += 24
        objetos = [
            (VERDE_JUGADOR, "Verde = Tu jugador"),
            (ROJO, "Rojo = Perseguidor (va hacia ti o el decoy)"),
            (AZUL_INVISIBLE, "Azul translucido = Invisible (casi no se ve)"),
            (ROJO, "Morado oscuro = Trampa (aplica debuff)"),
            (DORADO, "Dorado ? = Caja de habilidad"),
            (VERDE_JUGADOR, "Verde pequeno = Salida del nivel"),
        ]
        for color, texto in objetos:
            pygame.draw.rect(self.pantalla, color, (ANCHO // 2 - 220, y - 6, 12, 12))
            txt = self.fuente_tiny.render(texto, True, BLANCO)
            self.pantalla.blit(txt, (ANCHO // 2 - 200, y - 5))
            y += 22

        y += 10
        txt = self.fuente_pequena.render("HABILIDADES (Clic Derecho):", True, CIAN)
        self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
        y += 24
        habilidades = [
            (DORADO, "Inmunidad: 2s invulnerable"),
            (AZUL_INVISIBLE, "Congelar: 3s congelar enemigos"),
            (CIAN, "Sonar: 2.5s ver todo + resaltar enemigos/salida"),
            (NARANJA, "Decoy: 4s clon que atrae enemigos"),
        ]
        for color, texto in habilidades:
            txt = self.fuente_tiny.render(texto, True, color)
            self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
            y += 20

        y += 10
        txt = self.fuente_pequena.render("DEBUFFS (Trampas):", True, ROSA)
        self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
        y += 24
        debuffs = [
            (AMARILLO, "Ralentizacion: 50% velocidad por 4s"),
            (ROSA, "Ceguera: radio de luz a la mitad por 4s"),
            (NARANJA, "Invertidos: controles invertidos por 4s"),
        ]
        for color, texto in debuffs:
            txt = self.fuente_tiny.render(texto, True, color)
            self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
            y += 20

        self._botones["VOLVER"] = self._dibujar_boton("VOLVER", ANCHO // 2, ALTO - 50, 200, 48)

    def _dibujar_juego(self):
        """Dibuja el juego con camara, iluminacion y efectos."""
        # Dimensiones del mapa en pixeles
        map_w = self.level.columnas * TAM_CELDA
        map_h = self.level.filas * TAM_CELDA

        # Camara centrada en jugador
        self.camera_x = ANCHO // 2 - self.jugador.rect.centerx
        self.camera_y = ALTO // 2 - self.jugador.rect.centery

        # Claampear: que el mapa nunca se salga de la pantalla
        if map_w <= ANCHO:
            self.camera_x = (ANCHO - map_w) // 2
        else:
            self.camera_x = max(ANCHO - map_w, min(self.camera_x, 0))

        if map_h <= ALTO:
            self.camera_y = (ALTO - map_h) // 2
        else:
            self.camera_y = max(ALTO - map_h, min(self.camera_y, 0))

        # Superficie de juego (del tamano del mapa)
        if (self.superficie_juego.get_width() != map_w or
                self.superficie_juego.get_height() != map_h):
            self.superficie_juego = pygame.Surface((map_w, map_h))

        self.superficie_juego.fill(NEGRO)
        self.level.dibujar(self.superficie_juego)

        # Cajas
        for caja in self.cajas:
            caja.dibujar(self.superficie_juego)

        # Trampas
        for t in self.enemigos_manager.trampas:
            t.dibujar(self.superficie_juego)

        # Invisibles
        for i in self.enemigos_manager.invisibles:
            i.dibujar(self.superficie_juego)

        # Perseguidores
        for p in self.enemigos_manager.perseguidores:
            p.dibujar(self.superficie_juego)

        # Decoy
        if self.decoy:
            self.decoy.dibujar(self.superficie_juego)

        # Jugador
        self.jugador.dibujar(self.superficie_juego)

        # Blit de camara a pantalla
        self.pantalla.blit(self.superficie_juego, (self.camera_x, self.camera_y))

        # === SONAR: resaltar enemigos y salida ===
        if self.skill_manager.sonar_activo:
            self._dibujar_sonar_overlay()

        # === MASCARA DE OSCURIDAD ===
        if not self.skill_manager.sonar_activo:
            radio = RADIOS_LUZ[self.nivel_actual]
            debuff_ceguera = self.jugador.tiene_debuff(DEBUFF_BLINDNESS)
            # Centro de luz = posicion del jugador en pantalla
            lx = self.jugador.rect.centerx + self.camera_x
            ly = self.jugador.rect.centery + self.camera_y
            self.lighting.dibujar(self.pantalla, self.nivel_actual, int(lx), int(ly), radio, debuff_ceguera)

        # HUD
        self._dibujar_hud()

    def _dibujar_sonar_overlay(self):
        """Dibuja resplandor verde en salida y rojo en enemigos."""
        fuente = pygame.font.SysFont(None, 20)

        # Resaltar salida
        if self.level.posicion_salida:
            sx = self.level.posicion_salida[0] + self.camera_x
            sy = self.level.posicion_salida[1] + self.camera_y
            pygame.draw.rect(self.pantalla, VERDE_JUGADOR, (sx - 14, sy - 14, 28, 28), 3)
            t = fuente.render("SALIDA", True, VERDE_JUGADOR)
            self.pantalla.blit(t, (sx - t.get_width() // 2, sy - 25))

        # Resaltar perseguidores
        for p in self.enemigos_manager.perseguidores:
            px = p.rect.centerx + self.camera_x
            py = p.rect.centery + self.camera_y
            pygame.draw.circle(self.pantalla, ROJO, (int(px), int(py)), 20, 3)

        # Resaltar invisibles
        for i in self.enemigos_manager.invisibles:
            ix = i.rect.centerx + self.camera_x
            iy = i.rect.centery + self.camera_y
            pygame.draw.circle(self.pantalla, ROJO, (int(ix), int(iy)), 20, 3)

    def _dibujar_hud(self):
        """Dibuja la interfaz de usuario."""
        fuente = pygame.font.SysFont(None, 26)

        # Panel de vidas
        panel = pygame.Surface((160, 44), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        self.pantalla.blit(panel, (8, 8))

        # Corazones
        for i in range(VIDAS):
            x = 28 + i * 40
            if i < self.jugador.vidas:
                pygame.draw.circle(self.pantalla, ROJO, (x, 30), 12)
                pygame.draw.circle(self.pantalla, BLANCO, (x, 30), 12, 2)
            else:
                pygame.draw.circle(self.pantalla, GRIS_OSCURO, (x, 30), 12)
                pygame.draw.circle(self.pantalla, (80, 80, 80), (x, 30), 12, 2)

        txt_vidas = fuente.render(f"x{self.jugador.vidas}", True, BLANCO)
        self.pantalla.blit(txt_vidas, (140, 22))

        # Nivel
        txt_nivel = fuente.render(f"NIVEL {self.nivel_actual + 1}", True, BLANCO)
        self.pantalla.blit(txt_nivel, (ANCHO // 2 - txt_nivel.get_width() // 2, 10))

        # Habilidades
        self.skill_manager.dibujar_hud(self.pantalla)

        # Indicador de debuffs activos
        y_deb = 12
        if self.jugador.tiene_debuff(DEBUFF_SLOWDOWN):
            s = fuente.render("RALENTIZADO", True, AMARILLO)
            self.pantalla.blit(s, (ANCHO - s.get_width() - 15, y_deb))
            y_deb += 22
        if self.jugador.tiene_debuff(DEBUFF_BLINDNESS):
            s = fuente.render("CEGUERA", True, ROSA)
            self.pantalla.blit(s, (ANCHO - s.get_width() - 15, y_deb))
            y_deb += 22
        if self.jugador.tiene_debuff(DEBUFF_INVERTED):
            s = fuente.render("INVERTIDO", True, NARANJA)
            self.pantalla.blit(s, (ANCHO - s.get_width() - 15, y_deb))
            y_deb += 22

        # Indicador de salida (flecha parpadeante)
        if self.level.posicion_salida:
            t = pygame.time.get_ticks()
            if (t // 400) % 2 == 0:
                sx = self.level.posicion_salida[0] + self.camera_x
                sy = self.level.posicion_salida[1] + self.camera_y
                pygame.draw.polygon(self.pantalla, VERDE_JUGADOR, [
                    (sx, sy - 12), (sx - 8, sy + 4), (sx + 8, sy + 4)
                ])

    def ejecutar(self):
        """Bucle principal."""
        while True:
            self.manejar_eventos()
            self.actualizar()
            self.dibujar()
            self.reloj.tick(FPS)


if __name__ == "__main__":
    juego = Game()
    juego.ejecutar()
