import pygame
from random import randint

# general setup
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720 #Set the window dimensions
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT)) #Display Surface Dimensions
pygame.display.set_caption('Space Destroyer') #Calls the game "Space Destroyer"
running = True #Create a variable that equates to the game being active (Running)
 
# plain surface
surf = pygame.Surface((100,200))
surf.fill('purple')
x = 100

#importing an image 
player_surf = pygame.image.load('C:/Users/dtbij/OneDrive/Bureaublad/IB/Minor/Individual Project/Game/Space Game/images/player.png').convert_alpha()
star_surf = pygame.image.load('C:/Users/dtbij/OneDrive/Bureaublad/IB/Minor/Individual Project/Game/Space Game/images/star.png').convert_alpha()
star_positions = [(randint(0, WINDOW_WIDTH),randint(0, WINDOW_HEIGHT)) for i in range(20)]

while running: 
    #Event loop    ##Provides the ability to run and afterwards quit the application
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 


    #Draw the game
    display_surface.fill('gray61')
    for pos in star_positions:
        display_surface.blit(star_surf, pos)
    x += 0.1
    display_surface.blit(player_surf, (x,150))
    

    pygame.display.update() #Takes all the events as written before and places them on the display service



pygame.quit()




