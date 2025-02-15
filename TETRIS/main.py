from copy import deepcopy
from random import choice, randrange

import pygame
from shapes import figures

# Constants
W, H = 10, 18
TILE = 44
GAME_RES = W * TILE, H * TILE
RES = 740, 940
FPS = 60


class Figure:
    def __init__(self, figures):
        self.figures = figures
        self.next_blocks = deepcopy(choice(self.figures))
        self.next_color = self.choose_color()
        self.reset()

    def reset(self):
        self.blocks = deepcopy(self.next_blocks)  # Asigna los bloques correctamente
        self.color = self.next_color  # Asigna el color
        self.update_next_figure()  # Actualiza la siguiente figura correctamente

    def update_next_figure(self):
        # Genera una nueva figura siguiente
        self.next_blocks = deepcopy(choice(self.figures))
        self.next_color = self.choose_color()

    @staticmethod
    def choose_color():

        colors = [
            (255, 0, 0),  # Rojo
            (0, 255, 0),  # Verde
            (255, 255, 0),  # Amarillo
            (255, 165, 0),  # Naranja
            (128, 0, 128),  # Morado
        ]
        return choice(colors)  # Selección aleatoria de uno de los colores

    def rotate(self):
        center = self.blocks[0]
        rotated_blocks = deepcopy(self.blocks)
        for i in range(4):
            x = self.blocks[i].y - center.y
            y = self.blocks[i].x - center.x
            rotated_blocks[i].x = center.x - x
            rotated_blocks[i].y = center.y + y
        return rotated_blocks

    def update_position(self, dx, dy):
        for block in self.blocks:
            block.x += dx
            block.y += dy


class Board:
    def __init__(self):
        self.grid = [
            pygame.Rect(x * TILE, y * TILE, TILE, TILE)
            for x in range(W)
            for y in range(H)
        ]
        self.field = [[0 for _ in range(W)] for _ in range(H)]

    def is_valid_position(self, figure_blocks):
        for block in figure_blocks:
            if (
                block.x < 0
                or block.x >= W
                or block.y >= H
                or (block.y >= 0 and self.field[block.y][block.x])
            ):
                return False
        return True

    def place_figure(self, figure_blocks, color):
        for block in figure_blocks:
            self.field[block.y][block.x] = color

    def clear_lines(self):
        lines_cleared = 0  # Contador de líneas eliminadas
        new_field = [
            [0 for _ in range(W)] for _ in range(H)
        ]  # Crear un nuevo tablero vacío
        new_row = H - 1  # Índice de la nueva fila donde copiamos los datos

        for row in range(H - 1, -1, -1):  # Recorrer el tablero de abajo hacia arriba
            if not all(self.field[row]):  # Si la fila NO está llena, la copiamos
                new_field[new_row] = self.field[row]
                new_row -= 1
            else:
                lines_cleared += 1  # Contamos la fila eliminada

        self.field = new_field  # Actualizamos el tablero con el nuevo
        return lines_cleared

    def find_matches(self):
        matches = []
        # Buscar coincidencias horizontales
        for y in range(H):
            x = 0
            while x < W - 2:
                if (
                    self.field[y][x]
                    and self.field[y][x] == self.field[y][x + 1] == self.field[y][x + 2]
                ):
                    match = [(y, x), (y, x + 1), (y, x + 2)]
                    # Extender la coincidencia si hay más de 3
                    for dx in range(3, W - x):
                        if self.field[y][x] == self.field[y][x + dx]:
                            match.append((y, x + dx))
                        else:
                            break
                    matches.append(match)
                    x += len(match)  # Saltar las cajas ya revisadas
                else:
                    x += 1

        # Buscar coincidencias verticales
        for x in range(W):
            y = 0
            while y < H - 2:
                if (
                    self.field[y][x]
                    and self.field[y][x] == self.field[y + 1][x] == self.field[y + 2][x]
                ):
                    match = [(y, x), (y + 1, x), (y + 2, x)]
                    # Extender la coincidencia si hay más de 3
                    for dy in range(3, H - y):
                        if self.field[y][x] == self.field[y + dy][x]:
                            match.append((y + dy, x))
                        else:
                            break
                    matches.append(match)
                    y += len(match)  # Saltar las cajas ya revisadas
                else:
                    y += 1

        return matches

    def clear_matches(self):
        matches = self.find_matches()
        if not matches:
            return 0

        score = 0
        for match in matches:
            if len(match) == 3:
                # Eliminar 3 en línea
                for y, x in match:
                    self.field[y][x] = 0
                score += 100
            elif len(match) == 4:
                # Eliminar fila o columna completa
                if match[0][0] == match[1][0]:  # Misma fila
                    y = match[0][0]
                    for x in range(W):
                        self.field[y][x] = 0
                else:  # Misma columna
                    x = match[0][1]
                    for y in range(H):
                        self.field[y][x] = 0
                score += 300
            elif len(match) == 5:
                # Eliminar todas las cajas del mismo color
                color = self.field[match[0][0]][match[0][1]]
                for y in range(H):
                    for x in range(W):
                        if self.field[y][x] == color:
                            self.field[y][x] = 0
                score += 500
            elif len(match) >= 6:
                # Eliminar todo el tablero
                for y in range(H):
                    for x in range(W):
                        self.field[y][x] = 0
                score += 1000

        return score

    def apply_gravity(self):
        for x in range(W):
            # Recorre cada columna de abajo hacia arriba
            for y in range(H - 1, -1, -1):
                if self.field[y][x] == 0:
                    # Busca la caja más cercana arriba para hacerla caer
                    for y_above in range(y - 1, -1, -1):
                        if self.field[y_above][x] != 0:
                            self.field[y][x] = self.field[y_above][x]
                            self.field[y_above][x] = 0
                            break


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(RES)
        self.game_screen = pygame.Surface(GAME_RES)
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.figure = Figure(figures)
        self.score = 0
        self.record = self.get_record()
        self.anim_speed, self.anim_limit = 60, 2000
        self.anim_count = 0

        # Load assets
        self.bg = pygame.image.load("img/bg.jpg").convert()
        self.game_bg = pygame.image.load("img/bg2.jpg").convert()
        self.main_font = pygame.font.Font("font/font.ttf", 65)
        self.font = pygame.font.Font("font/font.ttf", 45)
        self.title_tetris = self.main_font.render(
            "TETRIS", True, pygame.Color("darkorange")
        )
        self.title_score = self.font.render("score:", True, pygame.Color("green"))
        self.title_record = self.font.render("record:", True, pygame.Color("purple"))

    def get_record(self):
        try:
            with open("record") as f:
                return f.readline()
        except FileNotFoundError:
            with open("record", "w") as f:
                f.write("0")
            return "0"

    def set_record(self):
        new_record = max(int(self.record), self.score)
        with open("record", "w") as f:
            f.write(str(new_record))

    def check_events(self):
        dx, rotate = 0, False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.set_record()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    dx = -1
                elif event.key == pygame.K_RIGHT:
                    dx = 1
                elif event.key == pygame.K_DOWN:
                    self.anim_limit = 100
                elif event.key == pygame.K_UP:
                    rotate = True
        return dx, rotate

    def run(self):
        while True:
            dx, rotate = self.check_events()
            self.screen.blit(self.bg, (0, 0))
            self.screen.blit(self.game_screen, (20, 20))
            self.game_screen.blit(self.game_bg, (0, 0))

            # Move figure horizontally
            self.figure.update_position(dx, 0)
            if not self.board.is_valid_position(self.figure.blocks):
                self.figure.update_position(-dx, 0)

            # Rotate figure
            if rotate:
                rotated_blocks = self.figure.rotate()
                if self.board.is_valid_position(rotated_blocks):
                    self.figure.blocks = rotated_blocks

            # Move figure down (gravity)
            self.anim_count += self.anim_speed
            if self.anim_count > self.anim_limit:
                self.anim_count = 0
                self.figure.update_position(0, 1)
                if not self.board.is_valid_position(self.figure.blocks):
                    self.figure.update_position(0, -1)
                    self.board.place_figure(self.figure.blocks, self.figure.color)

                    self.score += self.board.clear_matches()
                    self.board.apply_gravity()

                    self.anim_limit = max(2000, self.anim_limit)

                    lines_cleared = self.board.clear_lines()
                    self.score += {0: 0, 1: 100, 2: 300, 3: 700, 4: 1500}[lines_cleared]

                    # La figura actual toma la figura siguiente
                    self.figure.reset()
                    # Ahora generamos la nueva figura siguiente
                    self.figure.update_next_figure()

                    lines_cleared = self.board.clear_lines()
                    self.score += {0: 0, 1: 100, 2: 300, 3: 700, 4: 1500}[lines_cleared]
                    self.anim_limit = 2000

            # Draw grid
            [
                pygame.draw.rect(self.game_screen, (40, 40, 40), rect, 1)
                for rect in self.board.grid
            ]

            # Draw figure
            for block in self.figure.blocks:
                pygame.draw.rect(
                    self.game_screen,
                    self.figure.color,
                    pygame.Rect(block.x * TILE, block.y * TILE, TILE - 2, TILE - 2),
                )

            # Draw field
            for y, row in enumerate(self.board.field):
                for x, col in enumerate(row):
                    if col:
                        pygame.draw.rect(
                            self.game_screen,
                            col,
                            pygame.Rect(x * TILE, y * TILE, TILE - 2, TILE - 2),
                        )

            # Draw next figure
            for block in self.figure.next_blocks:
                pygame.draw.rect(
                    self.screen,
                    self.figure.next_color,
                    pygame.Rect(
                        block.x * TILE + 380, block.y * TILE + 185, TILE - 2, TILE - 2
                    ),
                )

            # Draw titles and score
            self.screen.blit(self.title_tetris, (485, -10))
            self.screen.blit(self.title_score, (535, 780))
            self.screen.blit(
                self.font.render(str(self.score), True, pygame.Color("white")),
                (550, 840),
            )
            self.screen.blit(self.title_record, (525, 650))
            self.screen.blit(
                self.font.render(self.record, True, pygame.Color("gold")), (550, 710)
            )

            # Verificar si el juego ha terminado
            if any(self.board.field[0]):
                self.set_record()
                self.__init__()

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()
