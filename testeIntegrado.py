import pygame
import cv2
import mediapipe as mp
from pyamaze import maze
import time
import numpy as np

# Inicializa o Pygame
pygame.init()
pygame.font.init()

# Função para criar o labirinto
def create_maze(rows, cols):
    labirinto = maze(rows, cols)
    labirinto.CreateMaze()
    return labirinto

# Configurações iniciais
rows, cols = 3, 5
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("Labirinto com Pygame - Controle por Mão")
clock = pygame.time.Clock()

# MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0)

# Função para atualizar o tamanho da célula e as posições
def update_cell_size_and_positions():
    global cell_size, maze_x_offset, maze_y_offset, start_pos, goal_pos
    cell_size = min(screen_width // cols, (screen_height - 100) // rows)  # Ajusta o tamanho da célula
    maze_x_offset = (screen_width - cols * cell_size) // 2
    maze_y_offset = (screen_height - rows * cell_size - 100) // 2
    start_pos = (maze_x_offset + cell_size // 2, maze_y_offset + cell_size // 2)
    goal_pos = (maze_x_offset + cols * cell_size - cell_size // 2, maze_y_offset + rows * cell_size - cell_size // 2)

labirinto = create_maze(rows, cols)
update_cell_size_and_positions()

game_started = False
game_over = False
victory = False
start_time = None

# Configuração da zona de controle
ZONE_MARGIN = 110
ZONE_COLOR = (0, 0, 255)

# Funções

def binarize_image(frame):
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_green, upper_green)
    mask = cv2.bitwise_not(mask)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    return mask

def draw_maze():
    screen.fill((0, 128, 0))
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            x, y = maze_x_offset + (c - 1) * cell_size, maze_y_offset + (r - 1) * cell_size
            cell = labirinto.maze_map[(r, c)]
            if cell['E'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x + cell_size, y), (x + cell_size, y + cell_size), 2)
            if cell['W'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x, y), (x, y + cell_size), 2)
            if cell['N'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x, y), (x + cell_size, y), 2)
            if cell['S'] == 0:
                pygame.draw.line(screen, (0, 0, 0), (x, y + cell_size ), (x + cell_size, y + cell_size), 2)

def draw_circle(pos, color, radius=8):
    pygame.draw.circle(screen, color, pos, radius)

def check_collision(x, y):
    cell_x, cell_y = (x - maze_x_offset) // cell_size + 1, (y - maze_y_offset) // cell_size + 1
    if cell_y < 1 or cell_y > rows or cell_x < 1 or cell_x > cols:
        return True
    
    cell = labirinto.maze_map[(cell_y, cell_x)]
    offset_x, offset_y = (x - maze_x_offset) % cell_size, (y - maze_y_offset) % cell_size

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

def draw_message(text, color):
    font = pygame.font.SysFont(None, 50)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
    screen.blit(text_surface, text_rect)

def draw_button(text, x, y, width, height, color, text_color):
    pygame.draw.rect(screen, color, (x, y, width, height))
    font = pygame.font.SysFont(None, 30)
    text_surface = font.render(text, True, text_color)
    screen.blit(text_surface, (x + (width - text_surface.get_width()) // 2, y + (height - text_surface.get_height()) // 2))

def is_button_pressed(mx, my, x, y, width, height):
    return x < mx < x + width and y < my < y + height

# Loop principal
running = True
while running:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    height, width, _ = frame.shape

    # Desenhar a zona de controle
    cv2.rectangle(frame, (ZONE_MARGIN, ZONE_MARGIN), (width - ZONE_MARGIN, height - ZONE_MARGIN), ZONE_COLOR, 2)
    
    # Criar imagem binarizada
    binary_frame = binarize_image(frame)

    # Empilhar as imagens (original e binarizada) lado a lado
    combined_frame = np.hstack((frame, cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)))

    # Exibir a imagem combinada
    cv2.imshow("Webcam - Original e Binarizada", combined_frame)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            screen_width, screen_height = event.w, event.h
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            update_cell_size_and_positions()

    screen.fill((0, 128, 0))
    draw_maze()

    draw_circle(start_pos, (0, 255, 0), radius=10)
    draw_circle(goal_pos, (0, 0, 255), radius=10)

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        finger_x = int(index_finger_tip.x * width)
        finger_y = int(index_finger_tip.y * height)

        # Mostrar bolinha azul na webcam
        cv2.circle(frame, (finger_x, finger_y), 10, (255, 0, 0), -1)

        # Restrição à zona de controle
        if ZONE_MARGIN < finger_x < width - ZONE_MARGIN and ZONE_MARGIN < finger_y < height - ZONE_MARGIN:
            norm_x = (finger_x - ZONE_MARGIN) / (width - 2 * ZONE_MARGIN) * screen_width
            norm_y = (finger_y - ZONE_MARGIN) / (height - 2 * ZONE_MARGIN) * screen_height
            x, y = int(norm_x), int(norm_y)

            if not game_started and not game_over:
                check_start_position(x, y)
                draw_circle((x, y), (255, 255, 0), radius=6)
            elif game_started and not game_over:
                if check_collision(x, y):
                    game_over = True
                    victory = False
                elif check_victory(x, y):
                    game_over = True
                    victory = True

                draw_circle((x, y), (255, 0, 0), radius=6)

    if game_over:
        if victory:
            draw_message("Você venceu!", (0, 255, 0))
            draw_button("Próxima Fase", screen_width // 2 - 75, screen_height // 2, 150, 50, (0, 255, 0), (255, 255, 255))
        else:
            draw_message("Você perdeu!", (255, 0, 0))
            draw_button("Recomeçar", screen_width // 2 - 175, screen_height // 2, 150, 50, (255, 0, 0), (255, 255, 255))
            draw_button("Sair", screen_width // 2 + 25, screen_height // 2, 150, 50, (0, 0, 0), (255, 255, 255))

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if victory and is_button_pressed(mx, my, screen_width // 2 - 75, screen_height // 2, 150, 50):
                rows += 1
                cols += 1
                labirinto = create_maze(rows, cols)
                update_cell_size_and_positions()
                game_started = False
                game_over = False
            elif not victory and is_button_pressed(mx, my, screen_width // 2 - 175, screen_height // 2, 150, 50):
                labirinto = create_maze(rows, cols)
                update_cell_size_and_positions()
                game_started = False
                game_over = False
            elif not victory and is_button_pressed(mx, my, screen_width // 2 + 25, screen_height // 2, 150, 50):
                running = False

    pygame.display.flip()
    clock.tick(30)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
