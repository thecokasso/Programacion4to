import math
import random
import os
import pygame
from pygame import mixer

# Cambiar el directorio de trabajo a la carpeta del archivo para cargar recursos correctamente
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Inicializar pygame y mixer
pygame.init()
try:
    mixer.init()
except Exception:
    pass

# Crear la ventana (800x600)
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Título e ícono
pygame.display.set_caption("Space Invader - Modos de Ataque")
try:
    icon = pygame.image.load('ufo.png')
    pygame.display.set_icon(icon)
except Exception:
    pass

# Fondo
try:
    background = pygame.image.load('background.png')
except Exception:
    background = None

# Jugador
try:
    playerImg = pygame.image.load('player.png')
except Exception:
    playerImg = pygame.Surface((64, 64))
    playerImg.fill((0, 255, 0))

playerX = 370
playerY = 480
playerX_change = 0

# Enemigos
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = 6

try:
    base_enemy_img = pygame.image.load('enemy.png')
except Exception:
    base_enemy_img = pygame.Surface((64, 64))
    base_enemy_img.fill((255, 0, 0))

for i in range(num_of_enemies):
    enemyImg.append(base_enemy_img)
    enemyX.append(random.randint(0, 736))
    enemyY.append(random.randint(50, 150))
    enemyX_change.append(4)
    enemyY_change.append(40)

# Bala
try:
    bulletImg = pygame.image.load('bullet.png')
except Exception:
    bulletImg = pygame.Surface((16, 32))
    bulletImg.fill((255, 255, 0))

# Lista para manejar múltiples balas activas (permite disparos triples y búmeran)
bullets = []

# Modos de Ataque
ATTACKS = [
    {"id": "recto", "label": "↑ Recto (1)", "desc": "1 disparo recto"},
    {"id": "triple", "label": "←/→ Triple (3)", "desc": "1 recto + 2 diagonales"},
    {"id": "bumeran", "label": "↓ Búmeran", "desc": "Va y vuelve"}
]
attack_mode = "recto"

# Sonidos
try:
    bulletSound = mixer.Sound("laser.wav")
except Exception:
    bulletSound = None

try:
    explosionSound = mixer.Sound("explosion.wav")
except Exception:
    explosionSound = None

# Fuentes
score_font = pygame.font.Font('freesansbold.ttf', 24)
over_font = pygame.font.Font('freesansbold.ttf', 64)
button_font = pygame.font.Font('freesansbold.ttf', 15)
tip_font = pygame.font.Font('freesansbold.ttf', 13)

score_value = 0
game_over = False

# Botones en la interfaz superior
attack_rects = [
    pygame.Rect(155, 10, 145, 32),
    pygame.Rect(310, 10, 155, 32),
    pygame.Rect(475, 10, 145, 32)
]
reset_button_rect = pygame.Rect(635, 10, 150, 32)
game_over_button_rect = pygame.Rect(290, 340, 220, 50)


def show_hud(mouse_pos):
    # Puntaje
    score = score_font.render(f"Score: {score_value}", True, (255, 255, 255))
    screen.blit(score, (15, 14))

    # Botones de selección de ataque
    for idx, att in enumerate(ATTACKS):
        rect = attack_rects[idx]
        is_selected = (attack_mode == att["id"])
        is_hover = rect.collidepoint(mouse_pos)

        if is_selected:
            bg_color = (255, 190, 0)
            text_color = (0, 0, 0)
            border_color = (255, 255, 255)
        elif is_hover:
            bg_color = (55, 80, 130)
            text_color = (255, 255, 255)
            border_color = (150, 180, 240)
        else:
            bg_color = (25, 35, 60)
            text_color = (200, 200, 200)
            border_color = (70, 90, 120)

        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(screen, border_color, rect, 2 if is_selected else 1, border_radius=6)

        label = button_font.render(att["label"], True, text_color)
        screen.blit(label, label.get_rect(center=rect.center))

    # Botón Reiniciar
    is_reset_hover = reset_button_rect.collidepoint(mouse_pos)
    reset_bg = (180, 50, 50) if is_reset_hover else (130, 30, 30)
    pygame.draw.rect(screen, reset_bg, reset_button_rect, border_radius=6)
    pygame.draw.rect(screen, (255, 255, 255), reset_button_rect, 1, border_radius=6)
    reset_lbl = button_font.render("Reiniciar (R)", True, (255, 255, 255))
    screen.blit(reset_lbl, reset_lbl.get_rect(center=reset_button_rect.center))

    # Barra inferior con ayuda de teclas
    tip_text = tip_font.render("Moverse: [A] / [D]  |  Disparar: [W]  |  Cambiar Ataque: Flechas [↑] [←/→] [↓]  |  Reset: [R]", True, (190, 200, 220))
    screen.blit(tip_text, tip_text.get_rect(center=(400, 582)))


def game_over_screen(mouse_pos):
    over_text = over_font.render("GAME OVER", True, (255, 50, 50))
    screen.blit(over_text, (200, 230))

    is_hover = game_over_button_rect.collidepoint(mouse_pos)
    btn_color = (200, 50, 50) if is_hover else (150, 30, 30)
    pygame.draw.rect(screen, btn_color, game_over_button_rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), game_over_button_rect, 2, border_radius=8)
    btn_text = button_font.render("Jugar de nuevo (R)", True, (255, 255, 255))
    screen.blit(btn_text, btn_text.get_rect(center=game_over_button_rect.center))


def player(x, y):
    screen.blit(playerImg, (x, y))


def enemy(x, y, i):
    screen.blit(enemyImg[i], (x, y))


def can_shoot():
    if game_over:
        return False
    # Si es búmeran, solo se permite uno a la vez hasta que regrese
    if attack_mode == "bumeran":
        for b in bullets:
            if b["type"] == "bumeran":
                return False
        return True
    # Para recto o triple, se puede disparar cuando la ráfaga anterior haya finalizado
    return len(bullets) == 0


def fire_attack():
    if not can_shoot():
        return

    if bulletSound:
        bulletSound.play()

    startX = playerX + 32
    startY = playerY

    if attack_mode == "recto":
        # 1 solo disparo derecho hacia arriba
        bullets.append({
            "type": "recto",
            "x": startX,
            "y": startY,
            "vx": 0,
            "vy": -10,
            "angle": 0,
            "returning": False
        })

    elif attack_mode == "triple":
        # 3 disparos simultáneos: 1 recto, 1 diagonal izquierda y 1 diagonal derecha
        # 1) Disparo central recto
        bullets.append({
            "type": "recto",
            "x": startX,
            "y": startY,
            "vx": 0,
            "vy": -10,
            "angle": 0,
            "returning": False
        })
        # 2) Disparo diagonal hacia la izquierda
        bullets.append({
            "type": "diag_izq",
            "x": startX,
            "y": startY,
            "vx": -5,
            "vy": -10,
            "angle": 25,
            "returning": False
        })
        # 3) Disparo diagonal hacia la derecha
        bullets.append({
            "type": "diag_der",
            "x": startX,
            "y": startY,
            "vx": 5,
            "vy": -10,
            "angle": -25,
            "returning": False
        })

    elif attack_mode == "bumeran":
        # 1 bala que va hacia arriba y luego regresa como búmeran
        bullets.append({
            "type": "bumeran",
            "x": startX,
            "y": startY,
            "vx": 0,
            "vy": -10,
            "angle": 0,
            "returning": False
        })


def draw_bullet(b):
    if b["type"] == "bumeran":
        rotated = pygame.transform.rotate(bulletImg, b["angle"])
        rect = rotated.get_rect(center=(int(b["x"]), int(b["y"])))
        screen.blit(rotated, rect)
    elif b["angle"] != 0:
        rotated = pygame.transform.rotate(bulletImg, b["angle"])
        rect = rotated.get_rect(center=(int(b["x"]), int(b["y"])))
        screen.blit(rotated, rect)
    else:
        screen.blit(bulletImg, (int(b["x"] - 8), int(b["y"] - 16)))


def isCollision(enemyX, enemyY, bX, bY):
    # Calcula la distancia desde el centro del enemigo (64x64) al centro de la bala
    enemy_center_x = enemyX + 32
    enemy_center_y = enemyY + 32
    distance = math.hypot(enemy_center_x - bX, enemy_center_y - bY)
    return distance < 35


def reset_game():
    global score_value, playerX, playerX_change, bullets, game_over
    score_value = 0
    playerX = 370
    playerX_change = 0
    bullets.clear()
    game_over = False
    for j in range(num_of_enemies):
        enemyX[j] = random.randint(0, 736)
        enemyY[j] = random.randint(50, 150)
        enemyX_change[j] = 4


# Bucle Principal del Juego
running = True
while running:
    clock.tick(60)

    # Fondo
    screen.fill((0, 0, 0))
    if background:
        screen.blit(background, (0, 0))

    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Clics con el mouse
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if reset_button_rect.collidepoint(event.pos):
                reset_game()
            elif game_over and game_over_button_rect.collidepoint(event.pos):
                reset_game()
            else:
                for idx, r in enumerate(attack_rects):
                    if r.collidepoint(event.pos):
                        attack_mode = ATTACKS[idx]["id"]

        # Teclas presionadas
        if event.type == pygame.KEYDOWN:
            # Movimiento con A y D
            if event.key == pygame.K_a:
                playerX_change = -5
            if event.key == pygame.K_d:
                playerX_change = 5

            # Disparar con W o ESPACIO
            if event.key == pygame.K_w or event.key == pygame.K_SPACE:
                fire_attack()

            # Reiniciar con la tecla R
            if event.key == pygame.K_r:
                reset_game()

            # Cambiar de ataque con las flechitas (y números 1, 2, 3)
            # Flecha Arriba: Disparo Recto (1)
            if event.key == pygame.K_UP or event.key == pygame.K_1:
                attack_mode = "recto"
            # Flecha Izquierda o Derecha: Disparo Triple (1 recto + 2 diagonales)
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_2):
                attack_mode = "triple"
            # Flecha Abajo: Búmeran (va y vuelve)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_3:
                attack_mode = "bumeran"

        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_a, pygame.K_d):
                playerX_change = 0

    if not game_over:
        # Movimiento del jugador
        playerX += playerX_change
        if playerX <= 0:
            playerX = 0
        elif playerX >= 736:
            playerX = 736

        # Actualización de enemigos
        for i in range(num_of_enemies):
            # Condición de Game Over si un enemigo llega abajo
            if enemyY[i] > 440:
                game_over = True
                break

            enemyX[i] += enemyX_change[i]
            if enemyX[i] <= 0:
                enemyX_change[i] = 4
                enemyY[i] += enemyY_change[i]
            elif enemyX[i] >= 736:
                enemyX_change[i] = -4
                enemyY[i] += enemyY_change[i]

            enemy(enemyX[i], enemyY[i], i)

        # Movimiento y colisiones de las balas
        for b in bullets[:]:
            if b["type"] == "bumeran":
                b["angle"] = (b["angle"] + 20) % 360  # Efecto de giro continuo
                if not b["returning"]:
                    b["y"] += b["vy"]  # Sube
                    if b["y"] <= 120:  # Altura máxima antes de regresar
                        b["returning"] = True
                        b["vy"] = 10   # Comienza a bajar
                else:
                    b["y"] += b["vy"]  # Baja hacia la nave
                    # Persigue levemente la posición horizontal de la nave
                    target_x = playerX + 32
                    if b["x"] < target_x:
                        b["x"] += 3
                    elif b["x"] > target_x:
                        b["x"] -= 3

                    # Atrapado por el jugador o salió de la pantalla por abajo
                    if b["y"] >= playerY or b["y"] >= 540:
                        if b in bullets:
                            bullets.remove(b)
                        continue
            else:
                # Movimiento para balas rectas y diagonales
                b["x"] += b["vx"]
                b["y"] += b["vy"]

                # Eliminar bala si sale de la pantalla
                if b["y"] <= -20 or b["x"] <= -20 or b["x"] >= 820:
                    if b in bullets:
                        bullets.remove(b)
                    continue

            # Comprobar colisiones de esta bala con cada enemigo
            bullet_removed = False
            for i in range(num_of_enemies):
                if isCollision(enemyX[i], enemyY[i], b["x"], b["y"]):
                    if explosionSound:
                        explosionSound.play()
                    score_value += 1
                    enemyX[i] = random.randint(0, 736)
                    enemyY[i] = random.randint(50, 150)

                    if b["type"] == "bumeran":
                        # Al impactar a un enemigo, el búmeran empieza a regresar
                        b["returning"] = True
                        b["vy"] = 10
                    else:
                        if b in bullets:
                            bullets.remove(b)
                        bullet_removed = True
                        break

            if not bullet_removed and b in bullets:
                draw_bullet(b)

    else:
        game_over_screen(mouse_pos)

    # Dibujar jugador e interfaz
    player(playerX, playerY)
    show_hud(mouse_pos)

    pygame.display.update()

pygame.quit()
