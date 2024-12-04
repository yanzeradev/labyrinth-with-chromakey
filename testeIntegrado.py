import pygame
import cv2
import mediapipe as mp
from pyamaze import maze
from tkinter import Tk, messagebox
import time

# Inicializa o labirinto
rows, cols = 10, 10
labirinto = maze(rows, cols)
labirinto.CreateMaze()

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
ZONE_MARGIN = 70  # Margem interna da zona de controle
ZONE_COLOR = (0, 0, 255)  # Vermelho

# Funções
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

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 128, 0))
    draw_maze()

    draw_circle(start_pos, (0, 255, 0), radius=12)
    draw_circle(goal_pos, (0, 0, 255), radius=12)

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        finger_x = int(index_finger_tip.x * width)
        finger_y = int(index_finger_tip.y * height)

        # Mostrar bolinha azul na webcam
        cv2.circle(frame, (finger_x, finger_y), 10, (255, 0, 0), -1)

        # Restrição à zona de controle
        if ZONE_MARGIN < finger_x < width - ZONE_MARGIN and ZONE_MARGIN < finger_y < height - ZONE_MARGIN:
            # Normaliza as coordenadas da zona de controle para o jogo
            norm_x = (finger_x - ZONE_MARGIN) / (width - 2 * ZONE_MARGIN) * screen.get_width()
            norm_y = (finger_y - ZONE_MARGIN) / (height - 2 * ZONE_MARGIN) * screen.get_height()
            x, y = int(norm_x), int(norm_y)

            if not game_started:
                check_start_position(x, y)
                draw_circle((x, y), (255, 255, 0))
            else:
                if check_collision(x, y):
                    pygame.quit()
                    cap.release()
                    cv2.destroyAllWindows()
                    root = Tk()
                    root.withdraw()
                    messagebox.showinfo("Fim de Jogo", "Você bateu na parede!")
                    root.destroy()
                    break

                if check_victory(x, y):
                    pygame.quit()
                    cap.release()
                    cv2.destroyAllWindows()
                    root = Tk()
                    root.withdraw()
                    messagebox.showinfo("Parabéns!", "Você venceu o jogo!")
                    root.destroy()
                    break

                draw_circle((x, y), (255, 0, 0))

    cv2.imshow("Webcam", frame)
    pygame.display.flip()
    clock.tick(30)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
