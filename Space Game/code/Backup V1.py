import pygame
from os.path import join
from random import randint, uniform

# ---------------------------
# Global Constants / Setup
# ---------------------------
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Space Destroyer - Machine Gun Powerup')
clock = pygame.time.Clock()
running = True

# Random powerup spawn timing (now 25–45 sec)
next_powerup_time = pygame.time.get_ticks() + randint(25000, 45000)

# Margin so powerups don’t appear on the exact border
SPAWN_MARGIN = 50

# ---------------------------
# Load Resources
# ---------------------------
background_surf = pygame.image.load(join('images', 'backgrnd.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor2.png')).convert_alpha()
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
ammo_powerup_surf = pygame.image.load(join('images', 'ammo_powerup.png')).convert_alpha()  # <-- Your powerup image

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
        self.default_cooldown = 400     # Normal cooldown (ms)
        self.powerup_cooldown = 100     # Faster “machine gun” cooldown (ms)
        self.cooldown_duration = self.default_cooldown
        
        self.can_shoot = True
        self.laser_shoot_time = 0
        
        # Powerup effect
        self.bullet_speed_multiplier = 1.0
        self.powerup_end_time = 0
        
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
    """
    A powerup that doubles the player's bullet speed and reduces cooldown for 15 seconds.
    It despawns itself automatically after 10 seconds if not picked up.
    """
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        # Track spawn time so we can despawn after 10s
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt):
        # If 10s have passed since spawn, kill this powerup
        if pygame.time.get_ticks() - self.spawn_time >= 10000:
            self.kill()


# ---------------------------
# Collision Logic
# ---------------------------
def collisions():
    global running
    # 1) Player vs Meteor
    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        running = False  # end game on collision

    # 2) Laser vs Meteor
    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collided_sprites:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            explosion_sound.play()

    # 3) Player vs AmmoPowerup
    powerup_hits = pygame.sprite.spritecollide(player, powerup_sprites, True, pygame.sprite.collide_mask)
    if powerup_hits:
        # Apply effect for 15 seconds:
        #  - Double bullet speed
        #  - Reduce cooldown to create "machine gun" effect
        current_time = pygame.time.get_ticks()
        player.bullet_speed_multiplier = 2.0
        player.cooldown_duration = player.powerup_cooldown
        player.powerup_end_time = current_time + 15000  # 15,000 ms = 15 seconds


def display_score():
    current_time = pygame.time.get_ticks()
    text_surf = font.render(str(current_time), True, 'whitesmoke')
    text_rect = text_surf.get_rect(midtop=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 700))
    display_surface.blit(text_surf, text_rect)


# ---------------------------
# Sprite Groups
# ---------------------------
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
powerup_sprites = pygame.sprite.Group()

player = Player(all_sprites)

# Custom meteor spawn events
meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, 250)  # meteors spawn every 250 ms

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
        if event.type == meteor_event:
            x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
            Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))

    # 2) Check if time to spawn a powerup (25–45 sec) & limit to max 2
    if current_time >= next_powerup_time and len(powerup_sprites) < 2:
        # Spawn away from borders using margin
        px_min = SPAWN_MARGIN
        px_max = WINDOW_WIDTH - ammo_powerup_surf.get_width() - SPAWN_MARGIN
        py_min = SPAWN_MARGIN
        py_max = WINDOW_HEIGHT - ammo_powerup_surf.get_height() - SPAWN_MARGIN
        
        px = randint(px_min, px_max)
        py = randint(py_min, py_max)
        AmmoPowerup(ammo_powerup_surf, (px, py), (all_sprites, powerup_sprites))
        
        # schedule next powerup spawn between 25–45 seconds
        next_powerup_time = current_time + randint(25000, 45000)

    # 3) Draw Background
    display_surface.blit(background_surf, (0, 0))

    # 4) Update & Collisions
    all_sprites.update(dt)
    collisions()

    # 5) Draw Sprites + Score
    all_sprites.draw(display_surface)
    display_score()

    pygame.display.update()

pygame.quit()
