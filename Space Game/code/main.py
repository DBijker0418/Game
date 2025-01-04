import pygame
from os.path import join
from random import randint, uniform

# ---------------------------
# Global Constants / Setup
# ---------------------------
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Space Destroyer')
clock = pygame.time.Clock()
running = True

# We'll start meteor spawns at 500 ms intervals
meteor_spawn_rate = 500

# We’ll track when to next ramp up difficulty
next_increase_time = pygame.time.get_ticks() + 20000  # every 20 seconds

# We'll keep the old powerup spawn logic
next_powerup_time = pygame.time.get_ticks() + randint(25000, 45000)

# Margin so powerups don’t appear on the exact border
SPAWN_MARGIN = 50

# ---------------------------
# Additional Score for Meteors
# ---------------------------
score_offset = 0  # We'll increment this by 1000 whenever a meteor is destroyed.

# ---------------------------
# Load Resources
# ---------------------------
background_surf = pygame.image.load(join('images', 'backgrnd2.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor2.png')).convert_alpha()
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
ammo_powerup_surf = pygame.image.load(join('images', 'ammo_powerup.png')).convert_alpha()
health_powerup_surf = pygame.image.load(join('images', 'health_powerup.png')).convert_alpha()  # NEW

font = pygame.font.Font(join('images', 'Oxanium-bold.ttf'), 40)

explosion_frames = [
    pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha()
    for i in range(21)
]

laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
laser_sound.set_volume(0.2)

explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
explosion_sound.set_volume(0.4)

game_music = pygame.mixer.Sound(join('audio', 'game_music.wav'))
game_music.set_volume(0.2)
game_music.play(loops=-1)

# ---------------------------
# Event Types
# ---------------------------
meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, meteor_spawn_rate)

health_powerup_event = pygame.event.custom_type()
pygame.time.set_timer(health_powerup_event, 20000)  # Spawns every 20s

# ---------------------------
# Sprite Classes
# ---------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player2.png')).convert_alpha()
        self.rect = self.image.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.25))
        
        # Movement
        self.direction = pygame.Vector2()
        self.speed = 300
        
        # Cooldowns
        self.default_cooldown = 400     # normal cooldown (ms)
        self.powerup_cooldown = 100     # faster “machine gun” cooldown (ms)
        self.cooldown_duration = self.default_cooldown
        
        self.can_shoot = True
        self.laser_shoot_time = 0
        
        # Powerup effect
        self.bullet_speed_multiplier = 1.0
        self.powerup_end_time = 0
        
        # Health
        self.max_health = 5   # <-- now 5 instead of 3
        self.health = 5       # start at full health
        
        # Mask for collisions
        self.mask = pygame.mask.from_surface(self.image)

    def laser_timer(self):
        """Check if enough time has passed so we can shoot again."""
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        # 1. Revert bullet speed and cooldown if powerup expired
        current_time = pygame.time.get_ticks()
        if current_time > self.powerup_end_time:
            self.bullet_speed_multiplier = 1.0
            self.cooldown_duration = self.default_cooldown

        # 2. Movement
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()
        
        self.rect.center += self.direction * self.speed * dt

        # 3. Shooting
        if keys[pygame.K_SPACE] and self.can_shoot:
            Laser(
                laser_surf,
                self.rect.midtop,
                (all_sprites, laser_sprites),
                self.bullet_speed_multiplier
            )
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            laser_sound.play()

        # Finally check if we can shoot again
        self.laser_timer()


class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups, speed_multiplier=1.0):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(midbottom=pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.base_speed = 400
        self.speed_multiplier = speed_multiplier

    def update(self, dt):
        # Move upwards, using our multiplier
        self.rect.centery -= (self.base_speed * self.speed_multiplier) * dt
        if self.rect.bottom < 0:
            self.kill()


class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000
        
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.rotation_speed = randint(20, 50)
        self.rotation = 0

    def update(self, dt):
        # Move
        self.rect.center += self.direction * self.speed * dt
        # Lifetime check
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()
        # Rotate
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center=self.rect.center)


class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index) % len(self.frames)]
        else:
            self.kill()


class AmmoPowerup(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        # Track spawn time so we can despawn after 10s
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt):
        if pygame.time.get_ticks() - self.spawn_time >= 10000:
            self.kill()


class HealthPowerup(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt):
        if pygame.time.get_ticks() - self.spawn_time >= 10000:
            self.kill()


# ---------------------------
# Collision Logic
# ---------------------------
def collisions():
    global running, score_offset
    # 1) Player vs Meteor
    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        # For each meteor that hits us, lose 1 health
        for _ in collision_sprites:
            player.health -= 1
        
        # If health is 0, game ends
        if player.health <= 0:
            running = False

    # 2) Laser vs Meteor
    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collided_sprites:
            # Kill the laser, spawn an explosion
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            explosion_sound.play()
            # Add +1000 each time a meteor is destroyed
            score_offset += 1000

    # 3) Player vs AmmoPowerup
    powerup_hits = pygame.sprite.spritecollide(player, ammo_powerup_sprites, True, pygame.sprite.collide_mask)
    if powerup_hits:
        current_time = pygame.time.get_ticks()
        player.bullet_speed_multiplier = 2.0
        player.cooldown_duration = player.powerup_cooldown
        player.powerup_end_time = current_time + 15000

    # 4) Player vs HealthPowerup
    health_hits = pygame.sprite.spritecollide(player, health_powerup_sprites, True, pygame.sprite.collide_mask)
    if health_hits:
        # Heal player by 2, up to max of 5
        player.health = min(player.health + 2, player.max_health)


# ---------------------------
# Display "Score" (Time + offset)
# ---------------------------
def display_score():
    current_time = pygame.time.get_ticks()
    total_score = current_time + score_offset  # combine original time-based system + meteor kills

    text_surf = font.render(str(total_score), True, 'whitesmoke')
    text_rect = text_surf.get_rect(midtop=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 700))
    display_surface.blit(text_surf, text_rect)


# ---------------------------
# Health Bar Under Player
# ---------------------------
def display_health_bar(surface, target_player):
    """Draws a small health bar under the player’s sprite."""
    bar_width  = 60
    bar_height = 8
    
    # Position the bar just below the player's sprite
    bar_x = target_player.rect.centerx - (bar_width // 2)
    bar_y = target_player.rect.bottom + 5

    # Colors
    outline_color = (255, 0, 0)  # red outline
    fill_color    = (0, 255, 0)  # green fill

    # Outline
    outline_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(surface, outline_color, outline_rect, 2)

    # Fill
    health_ratio = target_player.health / target_player.max_health
    health_ratio = max(0, min(health_ratio, 1))
    fill_width   = int(bar_width * health_ratio)
    fill_rect    = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
    pygame.draw.rect(surface, fill_color, fill_rect)


# ---------------------------
# Difficulty Ramp
# ---------------------------
def update_difficulty():
    global meteor_spawn_rate, next_increase_time
    current_time = pygame.time.get_ticks()
    if current_time >= next_increase_time:
        # Decrease meteor spawn rate (faster spawns), but not below 100 ms
        meteor_spawn_rate = max(100, meteor_spawn_rate - 50)
        pygame.time.set_timer(meteor_event, meteor_spawn_rate)
        
        # Decrease player's default cooldown slightly (faster fire), but not below 50 ms
        player.default_cooldown = max(50, player.default_cooldown - 25)
        
        # Next difficulty bump 20s from now
        next_increase_time = current_time + 20000


# ---------------------------
# Sprite Groups
# ---------------------------
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()

# We'll keep separate groups for the powerups to handle collisions individually
ammo_powerup_sprites = pygame.sprite.Group()
health_powerup_sprites = pygame.sprite.Group()

player = Player(all_sprites)

# ---------------------------
# Main Game Loop
# ---------------------------
while running:
    dt = clock.tick(60) / 1000
    current_time = pygame.time.get_ticks()

    # 1) Handle Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Meteor spawn
        if event.type == meteor_event:
            x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
            Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))

        # Health Powerup spawn (every 20s)
        if event.type == health_powerup_event:
            px = randint(SPAWN_MARGIN, WINDOW_WIDTH  - health_powerup_surf.get_width()  - SPAWN_MARGIN)
            py = randint(SPAWN_MARGIN, WINDOW_HEIGHT - health_powerup_surf.get_height() - SPAWN_MARGIN)
            HealthPowerup(health_powerup_surf, (px, py), (all_sprites, health_powerup_sprites))

    # 2) Check if time to spawn ammo powerup (25–45 sec) & limit to max 2
    if current_time >= next_powerup_time and len(ammo_powerup_sprites) < 2:
        px_min = SPAWN_MARGIN
        px_max = WINDOW_WIDTH  - ammo_powerup_surf.get_width()  - SPAWN_MARGIN
        py_min = SPAWN_MARGIN
        py_max = WINDOW_HEIGHT - ammo_powerup_surf.get_height() - SPAWN_MARGIN
        
        px = randint(px_min, px_max)
        py = randint(py_min, py_max)
        AmmoPowerup(ammo_powerup_surf, (px, py), (all_sprites, ammo_powerup_sprites))
        
        next_powerup_time = current_time + randint(25000, 45000)

    # 3) Increase difficulty over time
    update_difficulty()

    # 4) Draw Background
    display_surface.blit(background_surf, (0, 0))

    # 5) Update & Collisions
    all_sprites.update(dt)
    collisions()

    # 6) Draw Sprites
    all_sprites.draw(display_surface)

    # 7) Draw Health Bar Under Player
    display_health_bar(display_surface, player)

    # 8) Display Score
    display_score()

    pygame.display.update()

pygame.quit()
