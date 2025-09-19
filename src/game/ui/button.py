import pygame

class Button:
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 bg, bg_hover, fg):
        self.rect = rect
        self.text = text
        self.font = font
        self.bg = bg
        self.bg_hover = bg_hover
        self.fg = fg
        self._label = self.font.render(self.text, True, self.fg)
        self._label_rect = self._label.get_rect(center=self.rect.center)

    def draw(self, surface: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, self.bg_hover if hovered else self.bg, self.rect, border_radius=10)
        surface.blit(self._label, self._label_rect)

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False
