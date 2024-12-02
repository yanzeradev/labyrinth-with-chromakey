import cv2
import mediapipe as mp
import pygame
import sys
import time
import numpy as np

# Configurações do Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Configurações do Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Labirinto com dedo indicador")
clock = pygame.time.Clock()

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Desenho do labirinto
def draw_complex_maze():
    pygame.draw.rect(screen, BLACK, pygame.Rect(50, 50, 700, 500), 5)
    walls = [
        pygame.Rect(100, 100, 600, 20),
        pygame.Rect(100, 150, 20, 400),
        pygame.Rect(200, 150, 20, 300),
        pygame.Rect(300, 50, 20, 300),
        pygame.Rect(400, 300, 300, 20),
        pygame.Rect(500, 200, 20, 300),
        pygame.Rect(600, 100, 20, 400),
    ]
    for wall in walls:
        pygame.draw.rect(screen, BLACK, wall)
    return walls

# Função para esperar o jogador iniciar
def wait_for_start(player_position, initial_position, cap):
    start_time = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * 800)
                y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * 600)
                player_position = (x, y)

        screen.fill(WHITE)
        draw_complex_maze()
        pygame.draw.circle(screen, BLUE, initial_position, 10)
        pygame.draw.circle(screen, GREEN, player_position, 10)

        if (abs(player_position[0] - initial_position[0]) < 15 and
            abs(player_position[1] - initial_position[1]) < 15):
            if start_time is None:
                start_time = time.time()
            elif time.time() - start_time >= 3:
                font = pygame.font.SysFont(None, 55)
                text = font.render("Jogo Iniciado!", True, GREEN)
                screen.blit(text, (250, 250))
                pygame.display.flip()
                pygame.time.wait(1000)
                return
        else:
            start_time = None

        pygame.display.flip()
        clock.tick(30)

# Janela adicional para exibir a webcam com o dedo detectado
def show_webcam_with_marker(cap):
    ret, frame = cap.read()
    if not ret:
        return None

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * frame.shape[1])
            y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * frame.shape[0])
            cv2.circle(frame, (x, y), 10, RED, -1)

    return frame

# Função principal
def main():
    cap = cv2.VideoCapture(0)
    player_position = (75, 75)
    initial_position = (75, 75)
    walls = draw_complex_maze()

    wait_for_start(player_position, initial_position, cap)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * 800)
                y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * 600)
                player_position = (x, y)

        screen.fill(WHITE)
        draw_complex_maze()
        pygame.draw.circle(screen, BLUE, player_position, 10)

        for wall in walls:
            if wall.collidepoint(player_position):
                font = pygame.font.SysFont(None, 55)
                text = font.render("Colisão! Você perdeu!", True, RED)
                screen.blit(text, (200, 250))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False

        webcam_frame = show_webcam_with_marker(cap)
        if webcam_frame is not None:
            cv2.imshow("Webcam", webcam_frame)

        pygame.display.flip()
        clock.tick(30)

    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
