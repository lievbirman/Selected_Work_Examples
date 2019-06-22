import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, lo=(0,0,0), hi=(160, 160, 160)):

    color_select = np.zeros_like(img[:,:,0])
    above_thresh = (img[:,:,0] > lo[0]) \
                & (img[:,:,1] > lo[1]) \
                & (img[:,:,2] > lo[2])
    below_thresh = (img[:,:,0] < hi[0]) \
                & (img[:,:,1] < hi[1]) \
                & (img[:,:,2] < hi[2])
    good = above_thresh & below_thresh
    color_select[good] = 1
    return color_select
def color_thresh_rgb(img, lo=(0,0,0), hi=(160, 160, 160), color = (255,255,255)):

    color_select = np.zeros_like(img[:,:,:])
    above_thresh = (img[:,:,0] > lo[0]) \
                & (img[:,:,1] > lo[1]) \
                & (img[:,:,2] > lo[2])
    below_thresh = (img[:,:,0] < hi[0]) \
                & (img[:,:,1] < hi[1]) \
                & (img[:,:,2] < hi[2])
    good = above_thresh & below_thresh
    color_select[good] = color


    return color_select
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the
    # center bottom of the image.
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle)
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))

    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result
    return xpix_rotated, ypix_rotated
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale):
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result
    return xpix_translated, ypix_translated
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world
def perspect_transform(img, src, dst):

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image

    return warped
def perception_step(Rover):

    # 1) Define source and destination points for perspective transform
    dst_size = 5
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - bottom_offset],
                      [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - bottom_offset],
                      [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset],
                      [Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset],
                      ])
    # 2) Apply perspective transform
    warped = perspect_transform(Rover.img, source, destination)

    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    obstacle = color_thresh(warped,tuple([0, 0, 0]),tuple([45, 38, 28]))
    navigable =  color_thresh(warped,tuple([100, 100, 100]),tuple([255, 225, 225]))
    rock = color_thresh(warped,tuple([115, 90, 0]),tuple([165, 140, 39]))

    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    nav_rgb = color_thresh_rgb(warped,tuple([100, 100, 100]),tuple([255, 225, 225]), color = (0,255,0))
    rock_rgb = color_thresh_rgb(warped,tuple([80, 50, 0]),tuple([180, 150, 40]), color = (255,255,255))
    obs_rgb = color_thresh_rgb(warped,tuple([0, 0, 0]),tuple([100, 100, 100]),color=(0,0,255))

    vision = np.add(nav_rgb,rock_rgb)
    vision = np.add(vision,obs_rgb)
    Rover.vision_image = np.clip(vision, a_min = 0, a_max = 255)

    # 5) Convert map image pixel values to rover-centric coords
    xpix_o, ypix_o = rover_coords(obstacle)
    xpix_n, ypix_n = rover_coords(navigable)
    xpix_r, ypix_r = rover_coords(rock)

    # 6) Convert rover-centric pixel values to world coordinates
    #xo, yo = pix_to_world(xpix_o, ypix_o, Rover.pos[0], Rover.pos[1], Rover.yaw, len(Rover.worldmap[0]), 20)
    xn, yn = pix_to_world(xpix_n, ypix_n, Rover.pos[0], Rover.pos[1], Rover.yaw, len(Rover.worldmap[0]), 20)
    xr, yr = pix_to_world(xpix_r, ypix_r, Rover.pos[0], Rover.pos[1], Rover.yaw, len(Rover.worldmap[0]), 20)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
    #Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1

    if (0 < Rover.pitch < 0.4) or (359.6 < Rover.pitch < 360):

        Rover.worldmap[xr, yr, 1] = np.clip(Rover.worldmap[xr, yr, 1] + 100,0,255)
        Rover.worldmap[xr, yr, 0] = np.clip(Rover.worldmap[xr, yr, 0] + 100,0,255)
        Rover.worldmap[xn, yn, 2] += 1
    #Rover.worldmap[xr, yr,0] = 250
    #Rover.worldmap[xr, yr,1] = 0

    #Rover.worldmap = np.fliplr(Rover.worldmap)
    #Rover.worldmap = np.rot90(Rover.worldmap)

    # 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles
    rover_centric_pixel_distances,rover_centric_angles = to_polar_coords(xpix_n, ypix_n)
    Rover.nav_dists = rover_centric_pixel_distances
    Rover.nav_angles = rover_centric_angles

    rock_pixel_distances,rock_angles = to_polar_coords(xpix_r, ypix_r)
    Rover.rock_nav_dists = rock_pixel_distances
    Rover.rock_nav_angles = rock_angles

    return Rover
