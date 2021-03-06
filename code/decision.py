import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward':
            # Check the extent of navigable terrain
            if len(Rover.nav_dists) >= Rover.stop_forward:
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_dists) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'
            # Are we approaching a rock?
            if Rover.sample_dist != np.inf and Rover.sample_dist <= 30:
                Rover.mode = 'rock_picking'

            # Make sure robot is making progress
            if Rover.throttle > 0 and Rover.vel <= 0.01:
                Rover.stuck_epoch += 1
            else:
                Rover.stuck_epoch = 0 # Reset time the robot has been stuck.

            if Rover.stuck_epoch > 10:
                Rover.mode = 'recovery'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_dists) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_dists) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
        elif Rover.mode == 'rock_picking':
            Rover.rock_picking_epoch += 1

            if Rover.sample_dist < 18:
                Rover.brake = Rover.brake_set
                Rover.throttle = 0.0
                if Rover.near_sample and Rover.vel <= 0.01 and Rover.vel >= 0.0 and not Rover.picking_up:
                    Rover.rock_picking_epoch = 0
                    Rover.send_pickup = True
                    Rover.mode = 'post_pickup'

            if Rover.rock_picking_epoch >= 100:
                Rover.rock_picking_epoch = 0
                Rover.sample_dist = np.inf
                Rover.mode = 'recovery'

        elif Rover.mode == 'post_pickup':
            Rover.rock_picking_epoch += 1

            if Rover.picking_up == False:
                Rover.sample_dist = np.inf
                Rover.mode = 'stop'
            elif Rover.rock_picking_epoch >= 1000:
                Rover.rock_picking_epoch = 0
                Rover.sample_dist = np.inf
                Rover.mode = 'stop'

        elif Rover.mode == 'recovery':
            Rover.brake = 0
            Rover.steer = 0.0
            Rover.throttle = -0.2

            # If we have moved a bit backward lets try going forward again.
            Rover.recovery_epoch += 1

            if Rover.recovery_epoch > 20:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.stuck_epoch = 0
                Rover.mode = 'forward'
                Rover.recovery_epoch = 0

    return Rover