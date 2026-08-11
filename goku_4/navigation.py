import time
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('GOKU.Navigation')


class Direction(Enum):
    FORWARD = 'forward'
    LEFT = 'left'
    RIGHT = 'right'
    BACKWARD = 'backward'


class TrajectoryState(Enum):
    CLEAR = 'clear'
    OBSTACLE_DETECTED = 'obstacle_detected'
    REROUTING = 'rerouting'
    DESTINATION_REACHED = 'destination_reached'
    BLOCKED = 'blocked'


class Trajectory:
    def __init__(self, direction: Direction, duration: float = 2.0):
        self.direction = direction
        self.duration = duration
        self.remaining_duration = duration
        self.waypoints: List[Tuple[Direction, float]] = []

    def add_waypoint(self, direction: Direction, duration: float):
        self.waypoints.append((direction, duration))


class NavigationSystem:
    def __init__(self):
        self.current_trajectory: Optional[Trajectory] = None
        self.original_direction: Optional[Direction] = None
        self.obstacle_avoidance_active = False
        self.max_reroute_attempts = 3
        self.turn_duration = 1.0
        self.reverse_duration = 0.5

    def plan_directional_movement(self, direction: str, duration: float = 2.0) -> Trajectory:
        dir_map = {
            'forward': Direction.FORWARD,
            'backward': Direction.BACKWARD,
            'left': Direction.LEFT,
            'right': Direction.RIGHT,
        }
        direction_enum = dir_map.get(direction.lower().strip(), Direction.FORWARD)
        self.original_direction = direction_enum
        trajectory = Trajectory(direction_enum, duration)
        self.current_trajectory = trajectory
        logger.info(f"Planned trajectory: {direction} for {duration}s")
        return trajectory

    def check_path_clear(self) -> bool:
        return True

    def detect_obstacles(self) -> List[str]:
        return []

    def is_obstacle_in_path(self, direction: Direction) -> bool:
        return False

    def calculate_new_trajectory(self, direction: Direction, blocked_directions: List[str]) -> Optional[List[Tuple[Direction, float]]]:
        logger.info(f"Calculating new trajectory for {direction.value}")
        return [(Direction.RIGHT, self.turn_duration),
                (Direction.FORWARD, 1.5),
                (Direction.LEFT, self.turn_duration)]

    def execute_trajectory(self, motor_ctrl, trajectory: List[Tuple[Direction, float]]) -> bool:
        motor_map = {
            Direction.FORWARD: motor_ctrl.forward,
            Direction.BACKWARD: motor_ctrl.backward,
            Direction.LEFT: motor_ctrl.left,
            Direction.RIGHT: motor_ctrl.right,
        }

        for direction, duration in trajectory:
            move_func = motor_map.get(direction)
            if move_func:
                logger.info(f"Executing: {direction.value} for {duration}s")
                move_func()
                time.sleep(duration)
                motor_ctrl.stop()
                time.sleep(0.1)
            else:
                logger.error(f"Unknown direction: {direction}")
                return False
        return True

    def move_with_avoidance(self, motor_ctrl, direction: Direction, duration: float, tts_callback=None, display_callback=None) -> TrajectoryState:
        move_map = {
            Direction.FORWARD: motor_ctrl.forward,
            Direction.BACKWARD: motor_ctrl.backward,
            Direction.LEFT: motor_ctrl.left,
            Direction.RIGHT: motor_ctrl.right,
        }

        move_func = move_map.get(direction)
        if not move_func:
            return TrajectoryState.BLOCKED

        elapsed = 0
        step = 0.3

        while elapsed < duration:
            move_func()
            time.sleep(step)
            elapsed += step

        motor_ctrl.stop()
        return TrajectoryState.DESTINATION_REACHED

    def _get_opposite(self, direction: Direction) -> Direction:
        opposites = {
            Direction.FORWARD: Direction.BACKWARD,
            Direction.BACKWARD: Direction.FORWARD,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }
        return opposites.get(direction, Direction.BACKWARD)

    def autonomous_navigate(self, motor_ctrl, duration: float = 30.0, tts_callback=None, display_callback=None) -> TrajectoryState:
        nav_start = time.time()

        while (time.time() - nav_start) < duration:
            motor_ctrl.forward()
            time.sleep(1.0)
            motor_ctrl.stop()
            time.sleep(0.2)

        motor_ctrl.stop()
        return TrajectoryState.DESTINATION_REACHED


navigation_system = NavigationSystem()
