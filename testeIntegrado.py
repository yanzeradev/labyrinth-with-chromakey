import pygame
import cv2
import numpy as np
import mediapipe as mp
from pyamaze import maze
from tkinter import Tk, messagebox
import time

# Inicializa o labirinto
rows, cols = 9, 16
labirinto = maze(rows, cols)
labirinto.CreateMaze()

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)

# Configurações do pygame
pygame.init()
cell_size = 40
screen = pygame.display.set_mode((cols * cell_size, rows * cell_size))
pygame.display.set_caption("Labirinto com Pygame - Controle por Mão")
clock = pygame.time.Clock()

# MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0)

# Posições inicial e final
start_pos = (cell_size // 2, cell_size // 2)
goal_pos = (cols * cell_size - cell_size // 2, rows * cell_size - cell_size // 2)

game_started = False
start_time = None

# Configuração da zona de controle
ZONE_MARGIN = 130  # Margem interna da zona de controle
ZONE_COLOR = (0, 0, 255)  # Vermelho

# Função para binarizar a imagem
def binarize_frame(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([36, 25, 25])
    upper_green = np.array([70, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Aplicando um filtro para melhorar a detecção do verde
    mask = cv2.GaussianBlur(mask, (5, 5), 0)  # Filtro para reduzir o "chuvisco"
    
    mask_inv = cv2.bitwise_not(mask)
    _, img_binary = cv2.threshold(mask_inv, 127, 255, cv2.THRESH_BINARY)
    
    return img_binary

# Funções do labirinto e do jogo
def draw_maze():
    screen.fill((0, 128, 0))
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            x, y = (c - 1) * cell_size, (r - 1) * cell_size
            cell = labirinto.maze_map[(r, c)]
            if cell['E'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x + cell_size, y), (x + cell_size, y + cell_size), 2)
            if cell['W'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x, y), (x, y + cell_size), 2)
            if cell['N'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x, y), (x + cell_size, y), 2)
            if cell['S'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x, y + cell_size), (x + cell_size, y + cell_size), 2)

def draw_circle(pos, color, radius=8):
    pygame.draw.circle(screen, color, pos, radius)

def check_collision(x, y):
    cell_x, cell_y = x // cell_size + 1, y // cell_size + 1
    if cell_y < 1 or cell_y > rows or cell_x < 1 or cell_x > cols:
        return True
    
    cell = labirinto.maze_map[(cell_y, cell_x)]
    offset_x, offset_y = x % cell_size, y % cell_size

    if offset_x < 8 and not cell['W']:
        return True
    if offset_x > cell_size - 8 and not cell['E']:
        return True
    if offset_y < 8 and not cell['N']:
        return True
    if offset_y > cell_size - 8 and not cell['S']:
        return True
    
    return False

def check_start_position(x, y):
    global start_time, game_started
    if abs(x - start_pos[0]) < 20 and abs(y - start_pos[1]) < 20:
        if start_time is None:
            start_time = time.time()
        elif time.time() - start_time >= 3:
            game_started = True
    else:
        start_time = None

def check_victory(x, y):
    return abs(x - goal_pos[0]) < 20 and abs(y - goal_pos[1]) < 20

def draw_buttons():
    """Desenha os botões na tela."""
    button_font = pygame.font.SysFont(None, 40)
    # Botão "Recomeçar"
    pygame.draw.rect(screen, GREEN, restart_button_rect)
    restart_text = button_font.render("Recomeçar", True, BLACK)
    screen.blit(restart_text, (restart_button_rect.x + 10, restart_button_rect.y + 10))

    # Botão "Sair"
    pygame.draw.rect(screen, RED, quit_button_rect)
    quit_text = button_font.render("Sair", True, BLACK)
    screen.blit(quit_text, (quit_button_rect.x + 40, quit_button_rect.y + 10))


def show_message(text, color):
    """Exibe uma mensagem no centro da tela com botões de ação."""
    font = pygame.font.SysFont(None, 55)
    message = font.render(text, True, color)
    text_rect = message.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
    screen.blit(message, text_rect)
    draw_buttons()


# Retângulos dos botões (para controle de clique)
button_width, button_height = 150, 50
restart_button_rect = pygame.Rect(
    (screen.get_width() // 2 - button_width - 10, screen.get_height() // 2),
    (button_width, button_height),
)
quit_button_rect = pygame.Rect(
    (screen.get_width() // 2 + 10, screen.get_height() // 2),
    (button_width, button_height),
)

# Variável para controlar o estado do jogo
game_state = "playing"

# Loop principal
running = True
while running:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    # Desenhando o limite em vermelho na imagem original (antes da binarização)
    height, width = frame.shape[:2]
    cv2.rectangle(frame, (ZONE_MARGIN, ZONE_MARGIN), (width - ZONE_MARGIN, height - ZONE_MARGIN), (0, 0, 255), 2)

    # Detecção da mão
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Binarização da imagem
    binarized_frame = binarize_frame(frame)

    # Exibe a imagem binarizada
    cv2.imshow('Imagem Binarizada', binarized_frame)

    # Processamento do pygame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state != "playing":  # Detecta cliques nos botões
                mouse_pos = pygame.mouse.get_pos()
                if restart_button_rect.collidepoint(mouse_pos):
                    # Reinicia o jogo
                    game_started = False
                    start_time = None
                    game_state = "playing"
                elif quit_button_rect.collidepoint(mouse_pos):
                    # Sai do jogo
                    running = False

    if game_state == "playing":
        screen.fill((0, 128, 0))
        draw_maze()

        draw_circle(start_pos, (0, 255, 0), radius=12)
        draw_circle(goal_pos, (0, 0, 255), radius=12)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            finger_x = int(index_finger_tip.x * width)
            finger_y = int(index_finger_tip.y * height)

            if ZONE_MARGIN < finger_x < width - ZONE_MARGIN and ZONE_MARGIN < finger_y < height - ZONE_MARGIN:
                norm_x = (finger_x - ZONE_MARGIN) / (width - 2 * ZONE_MARGIN) * screen.get_width()
                norm_y = (finger_y - ZONE_MARGIN) / (height - 2 * ZONE_MARGIN) * screen.get_height()
                x, y = int(norm_x), int(norm_y)

                if not game_started:
                    check_start_position(x, y)
                    draw_circle((x, y), (255, 255, 0))
                else:
                    if check_collision(x, y):
                        game_state = "lost"
                    elif check_victory(x, y):
                        game_state = "won"
                    else:
                        draw_circle((x, y), (255, 0, 0))

    else:
        # Exibe a mensagem dependendo do estado do jogo
        if game_state == "lost":
            screen.fill(BLACK)
            show_message("Colisão! Você perdeu!", RED)
        elif game_state == "won":
            screen.fill(BLACK)
            show_message("Parabéns! Você venceu!", GREEN)

    pygame.display.flip()
    clock.tick(30)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()

