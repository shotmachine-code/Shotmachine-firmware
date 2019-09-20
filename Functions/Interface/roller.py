import pygame
import os
from random import randint


class Roller:

    def __init__(self, _posx, _posy, _roller_height, _roller_width, _roll_images_dir):
        # Prepare some variables
        self.posy = _posy
        self.roller_height = _roller_height
        self.brake = False
        self.brake_request = False
        self.Roll_images = []
        self.cont_dy = 0
        self.brakedistancei = 8  # amount of images used to come to a full stop
        self.stopimageindex = 0
        self.brakedistancey = 0
        self.brakespeed = 0
        self.Shadow_image = 'Functions/Interface/Images/Roller_shadow.png'

        # Load roller images
        filelist = os.listdir(_roll_images_dir)

        for i in range(len(filelist)):
            try:
                #print(fichier.endswith)
                #if not fichier.endswith(".png") and not fichier.endswith(".jpg") and not fichier.endswith(".jpeg"):
                #filelist.remove(fichier)
                #for i in range(len(filelist)):
                imagepath = os.path.join(_roll_images_dir, filelist[i])
                #print(imagepath)
                image = pygame.image.load(imagepath).convert()
                self.Roll_images.append(pygame.transform.scale(image, (_roller_width, _roller_width)))
            except:
                continue
        if len(filelist) < 4:
            print('Error: Not enough roll images in folder. Need al least 4 images')
        self.n_roll_images = len(self.Roll_images)
        self.rollerheight = self.Roll_images[0].get_height()

        # Load shadow images
        fade_image_load = pygame.image.load(self.Shadow_image).convert_alpha()
        self.fade_image_top = pygame.transform.scale(fade_image_load,
                                                     (round(_roller_width * 1.1), round(self.roller_height / 5)))
        self.fade_image_bottom = pygame.transform.rotate(self.fade_image_top, 180)
        self.fade_image_height = self.fade_image_bottom.get_height()

        # Determine a random starting position
        self.imageindex_1 = randint(0, self.n_roll_images-1)
        self.imageindex_2 = (self.imageindex_1 + 1) % self.n_roll_images
        self.imageindex_3 = (self.imageindex_1 + 2) % self.n_roll_images

        # Determine the exact starting positions of the images
        self.roll_1_y = self.posy - (1.5 * self.rollerheight)
        self.roll_2_y = self.roll_1_y + self.rollerheight
        self.roll_3_y = self.roll_2_y + self.rollerheight
        self.Roll_posx_left = _posx - _roller_width / 2
        self.Roll_posy_top = self.posy - self.roller_height / 2

        # Determine bounding box around roller
        self.roll_boundingbox = pygame.Rect(self.Roll_posx_left, self.Roll_posy_top,
                                            _roller_width, self.roller_height)

    #def set_reset_roller(self):
    #    # Reset roller and start rolling
    #    self.brake = False
    #    self.brake_request = False

    def draw_roller(self):
        # Print roll images to screen buffer:
        screenref = pygame.display.get_surface()
        screenref.blit(self.Roll_images[self.imageindex_1], [self.Roll_posx_left, self.roll_1_y])
        screenref.blit(self.Roll_images[self.imageindex_2], [self.Roll_posx_left, self.roll_2_y])
        screenref.blit(self.Roll_images[self.imageindex_3], [self.Roll_posx_left, self.roll_3_y])

        # Print bounding box and shadows to screen buffer
        screenref.blit(self.fade_image_top, [self.Roll_posx_left - 15, self.Roll_posy_top - 10])
        screenref.blit(self.fade_image_bottom,
                       [self.Roll_posx_left - 15,
                        self.Roll_posy_top + self.roller_height - self.fade_image_height + 10])
        pygame.draw.rect(screenref, (0, 0, 0), self.roll_boundingbox, 5)
        return self.roll_boundingbox

    def start_roller(self,dy):
        self.cont_dy = dy
        self.brake = False
        self.brake_request = False

    def stop_roller_smooth(self, stopimage_i):
        # function to initialize braking of the roller
        self.brake_request = True
        self.stopimageindex = stopimage_i % self.n_roll_images

    def stop_roller_direct(self,imageindex):
        self.cont_dy = 0
        self.roll_1_y = self.posy - (1.5 * self.rollerheight)
        self.roll_2_y = self.roll_1_y + self.rollerheight
        self.roll_3_y = self.roll_2_y + self.rollerheight
        self.imageindex_1 = imageindex % self.n_roll_images-1
        self.imageindex_2 = self.imageindex_1 + 1 % self.n_roll_images-1
        self.imageindex_3 = self.imageindex_1 + 2 % self.n_roll_images-1

    def update_roller(self):
        # Rotate the roller images if needed
        # Calculate new positions of the images
        if self.brake:
            self.cont_dy = self.cont_dy-self.brakespeed
            if self.cont_dy <= 0.5:
                self.brake = False
                self.cont_dy = 0
        discrete_dy = round(self.cont_dy)
        self.roll_1_y += discrete_dy
        self.roll_2_y += discrete_dy
        self.roll_3_y += discrete_dy

        # Check if one of the images is out of view(down), if so, move to top and change image
        if self.roll_1_y > self.posy + self.rollerheight:
            self.roll_1_y = self.roll_1_y - 3 * self.rollerheight
            self.imageindex_1 = (self.imageindex_1 + 1) % self.n_roll_images
            # if stoprequest has been made, calculate how fast we must brake and start braking
            if self.brake_request and (self.imageindex_1 == self.stopimageindex):
                self.brake = True
                self.brake_request = False
                self.brakedistancey = self.brakedistancei*self.rollerheight
                self.brakedistancey = self.brakedistancey - (self.roll_1_y - self.posy + self.rollerheight)
                self.brakespeed = (self.cont_dy * self.cont_dy) / self.brakedistancey

        if self.roll_2_y > self.posy + self.rollerheight:
            self.roll_2_y = self.roll_2_y - 3 * self.rollerheight
            self.imageindex_2 = randint(0, self.n_roll_images-1)

        if self.roll_3_y > self.posy + self.rollerheight:
            self.roll_3_y = self.roll_3_y - 3 * self.rollerheight
            self.imageindex_3 = randint(0, self.n_roll_images-1)
        # Print roll images to screen buffer:
        screenref = pygame.display.get_surface()
        screenref.blit(self.Roll_images[self.imageindex_1], [self.Roll_posx_left, self.roll_1_y])
        screenref.blit(self.Roll_images[self.imageindex_2], [self.Roll_posx_left, self.roll_2_y])
        screenref.blit(self.Roll_images[self.imageindex_3], [self.Roll_posx_left, self.roll_3_y])

        # Print bounding box and shadows to screen buffer
        screenref.blit(self.fade_image_top, [self.Roll_posx_left - 15, self.Roll_posy_top - 10])
        screenref.blit(self.fade_image_bottom,
                       [self.Roll_posx_left - 15,
                        self.Roll_posy_top + self.roller_height - self.fade_image_height + 10])
        pygame.draw.rect(screenref, (0, 0, 0), self.roll_boundingbox, 5)

        # Return bounding box of roller in case something has changed, otherwise return nothing
        if discrete_dy == 0:
            result = None
        else:
            result = self.roll_boundingbox
        return result