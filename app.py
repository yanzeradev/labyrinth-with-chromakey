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
GRAY = (200, 200, 200)

# Desenho do labirinto
def draw_complex_maze():
    """
    Desenha o labirinto com paredes.
    """
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

def wait_for_start(player_position, initial_position, cap):
    """
    Espera o jogador colocar o dedo no ponto inicial do labirinto para começar.
    """
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

def show_webcam_with_marker(cap):
    """
    Mostra a webcam com o marcador no dedo indicador.
    """
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

def draw_buttons():
    """
    Desenha os botões de 'Recomeçar' e 'Sair' na tela.
    """
    restart_button = pygame.Rect(200, 300, 150, 50)
    quit_button = pygame.Rect(450, 300, 150, 50)
    pygame.draw.rect(screen, GRAY, restart_button)
    pygame.draw.rect(screen, GRAY, quit_button)
    font = pygame.font.SysFont(None, 40)
    screen.blit(font.render("Recomeçar", True, BLACK), (210, 310))
    screen.blit(font.render("Sair", True, BLACK), (485, 310))
    return restart_button, quit_button

def check_victory(player_position, exit_position):
    """
    Verifica se o jogador alcançou a saída do labirinto.
    """
    return (abs(player_position[0] - exit_position[0]) < 15 and
            abs(player_position[1] - exit_position[1]) < 15)

# Função principal
def main():
    cap = cv2.VideoCapture(0)
    player_position = (75, 75)
    initial_position = (75, 75)
    exit_position = (725, 525)  # Posição da saída do labirinto
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
        pygame.draw.circle(screen, GREEN, exit_position, 10)  # Desenha a saída do labirinto

        # Verifica vitória
        if check_victory(player_position, exit_position):
            font = pygame.font.SysFont(None, 55)
            text = font.render("Você venceu!", True, GREEN)
            screen.blit(text, (250, 250))
            pygame.display.flip()
            pygame.time.wait(2000)
            running = False

        # Verifica colisão com as paredes
        for wall in walls:
            if wall.collidepoint(player_position):
                font = pygame.font.SysFont(None, 55)
                text = font.render("Colisão! Você perdeu!", True, RED)
                screen.blit(text, (200, 250))
                pygame.display.flip()
                pygame.time.wait(2000)
                restart_button, quit_button = draw_buttons()
                pygame.display.flip()

                # Espera o jogador escolher entre recomeçar ou sair
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if restart_button.collidepoint(event.pos):
                                main()  # Recomeça o jogo
                            elif quit_button.collidepoint(event.pos):
                                cap.release()
                                pygame.quit()
                                sys.exit()

        webcam_frame = show_webcam_with_marker(cap)
        if webcam_frame is not None:
            cv2.imshow("Webcam", webcam_frame)
            cv2.moveWindow("Webcam", 900, 100)

        pygame.display.flip()
        clock.tick(30)

    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
