import numpy as np
import cv2

# Identify pixels containing rocks based on the HSV color.  
def rock_filter(img):

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # Yellowish color range
    low = np.array([20, 100, 100])
    high = np.array([30, 255, 255])

    fltr = cv2.inRange(hsv, low, high)

    result = np.zeros_like(hsv[:, :, 1])
    result[fltr.nonzero()] = 1
    
    return result


def terrain_filter(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    terrain = np.zeros_like(img[:,:,0])
    obstacles = np.zeros_like(img[:, :, 0])
    
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    
    # Index the array of zeros with the boolean array and set to 1
    terrain[above_thresh] = 1
    obstacles[~above_thresh] = 1
    
    # Return the binary image
    return terrain, obstacles


# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[0]).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to apply a rotation to pixel positions
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

# Define a function to perform a translation
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
     # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated

# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
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

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    # 1) Define source and destination points for perspective transform
    # 2) Apply perspective transform
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,1] = rock_sample color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image

    # 5) Convert map image pixel values to rover-centric coords
    # 6) Convert rover-centric pixel values to world coordinates
    # 7) Update Rover worldmap (to be displayed on right side of screen)
        # Example: Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        #          Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1

    # 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles
        # Rover.nav_dists = rover_centric_pixel_distances
        # Rover.nav_angles = rover_centric_angles

    image = Rover.img
    yaw = Rover.yaw
    xpos, ypos = Rover.pos

    # These source and destination points are defined to warp the image
    # to a grid where each 10x10 pixel square represents 1 square meter
    # The destination box will be 2*dst_size on each side
    dst_size = 5 

    # Set a bottom offset to account for the fact that the bottom of the image 
    # is not the position of the rover but a bit in front of it
    # this is just a rough guess, feel free to change it!
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset], 
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])

    warped = perspect_transform(image, source, destination)

    rock_img = rock_filter(warped)
    navigable_img, obstacle_img = terrain_filter(warped)

    Rover.vision_image[:, :, 0] = obstacle_img * 255;
    Rover.vision_image[:, :, 1] = rock_img * 255; 
    Rover.vision_image[:, :, 2] = navigable_img * 255;
    
    navigable_x_rover, navigable_y_rover = rover_coords(navigable_img)
    obstacle_x_rover, obstacle_y_rover = rover_coords(obstacle_img)
    rock_x_rover, rock_y_rover = rover_coords(rock_img)

    navigable_x_world, navigable_y_world = pix_to_world(navigable_x_rover,
                                                        navigable_y_rover, 
                                                        xpos, 
                                                        ypos, 
                                                        yaw, 
                                                        200, 
                                                        dst_size * 2)

    obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_x_rover, 
                                                      obstacle_y_rover, 
                                                      xpos, 
                                                      ypos, 
                                                      yaw, 
                                                      200, 
                                                      10)

    rock_x_world, rock_y_world = pix_to_world(rock_x_rover, 
                                              rock_y_rover, 
                                              xpos, 
                                              ypos, 
                                              yaw, 
                                              200, 
                                              10)

    # Only update the world map if the Rover's pitch/roll angles are within a given range
    should_update_worldmap = True

    if Rover.pitch >= 0.5 and Rover.pitch < 359:
        should_update_worldmap = False

    if Rover.roll >= 0.5 and Rover.roll < 359:
        should_update_worldmap = False

    if should_update_worldmap:
        Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1

    dist, angles = to_polar_coords(navigable_x_rover, navigable_y_rover)

    idx = np.where((angles >= -5) & (angles <= 30))
    Rover.nav_dists = dist[idx]
    Rover.nav_angles = angles[idx]

    # Compute the distance to a rock, if the rock is present, try to move twoards the rock.
    if(np.count_nonzero(rock_x_rover) + np.count_nonzero(rock_y_rover)) > 20:
        rock_dist, rock_angles = to_polar_coords(rock_x_rover, rock_y_rover)
        Rover.nav_angles = rock_angles
        Rover.sample_dist = np.mean(rock_dist)
    else:
        Rover.sample_dist = np.inf

    return Rover