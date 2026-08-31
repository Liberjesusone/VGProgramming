import random
import settings

class GameMode:
    def log_spawn_time(self) -> float:
        return 0;

    def next_log_y(self, last_log_y: float) -> float:
        return 0

    def ground_speed(self, dt: float) -> float:
        return 0

    def should_appear_log_pair(self) -> bool:
        return True

    def aperture(self) -> float:
        return 0

    def allow_hor_movement(self) -> bool:
        return False

    def allow_power_up(self) -> bool:
        return False

    def power_up_spawn_time(self) -> float:
        return 0.0

    def next_power_up_y(self) -> int:
        return 0

class NormalMode(GameMode):
    def log_spawn_time(self) -> float:
        return settings.TIME_TO_SPAWN_LOGS

    def next_log_y(self, last_log_y: float) -> float:
        return last_log_y + random.randint(-20, 20)

    def ground_speed(self, dt: float) -> float:
            return -settings.MAIN_SCROLL_SPEED * dt

    def should_appear_log_pair(self) -> bool:
        return True

    def aperture(self) -> float:
        return settings.LOGS_GAP

class HardMode(GameMode):
    def __init__(self) -> None:
        self.last_log_time = 0.0
        self.last_log_diff = 0.0
        self.logs_count = 0

    def log_spawn_time(self) -> float:
        self.last_log_time = settings.TIME_TO_SPAWN_LOGS + random.uniform(-0.40, 0.20)
        self.logs_count += 1
        return self.last_log_time

    def next_log_y(self, last_log_y: float) -> float:
        if self.last_log_time >= 1.4:
            return last_log_y + random.randint(-120, 120)
        else: 
            return last_log_y + random.randint(-40, 40)

    def ground_speed(self, dt: float) -> float:
        return -settings.MAIN_SCROLL_SPEED * dt - self.logs_count / 10 * dt 

    def should_appear_log_pair(self) -> bool:
        return random.randint(0,3) != 0   # 25% of times is dynamic log pair

    def aperture(self) -> float:
        return settings.LOGS_GAP + random.randint(-25,40)

    def allow_hor_movement(self) -> bool:
        return True

    def allow_power_up(self) -> bool:
        return True

    def power_up_spawn_time(self) -> float:
        return settings.POWER_UP_SPAWN_TIME + random.randint(-2, 2)

    def next_power_up_y(self) -> int:
        return random.randint(10, settings.VIRTUAL_HEIGHT - settings.POWER_UP_HEIGHT - 10)