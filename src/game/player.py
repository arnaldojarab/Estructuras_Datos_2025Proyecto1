import pygame

class Player:
    def __init__(self, cell_pos):
        self.x = cell_pos[0]*64 + 32
        self.y = cell_pos[1]*64 + 32
        self.radius = 12

    def pixel_move(self, dx, dy):
        self.x += dx
        self.y += dy

    def draw(self, screen):
        pygame.draw.circle(screen, (200, 230, 255), (int(self.x), int(self.y)), self.radius)
