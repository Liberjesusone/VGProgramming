import pygame
import settings

class PowerUp:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.vx = 0.0

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, settings.POWER_UP_WIDTH, settings.POWER_UP_HEIGHT);

    def collides(self, rect: pygame.Rect) -> bool:
        return self.get_rect().colliderect(rect)

    def update(self, dt: float):
        self.x -= settings.POWER_UP_SPEED * dt

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["power_up"], self.get_rect())