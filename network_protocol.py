"""
Network Protocol Definitions for LAN Multiplayer
Defines message types and formats for host-client communication
"""

from enum import Enum

class MessageType(Enum):
    """Types of messages that can be sent over the network"""
    # Client to Host
    INPUT = "input"                  # Player input (direction change)
    READY = "ready"                  # Client is ready to start
    
    # Host to Client
    GAME_STATE = "game_state"        # Full game state update
    GAME_START = "game_start"        # Game is starting
    GAME_END = "game_end"            # Game has ended
    PLAYER_ASSIGNED = "player_assigned"  # Assign player ID to client
    
    # Bidirectional
    PING = "ping"                    # Keep-alive
    PONG = "pong"                    # Keep-alive response

# Message Format Examples:
# 
# INPUT (Client -> Host):
# {
#     "type": "input",
#     "player_id": 1,
#     "direction": "UP",  # or "DOWN", "LEFT", "RIGHT"
#     "timestamp": 12345
# }
#
# GAME_STATE (Host -> Clients):
# {
#     "type": "game_state",
#     "snakes": [
#         {
#             "player_id": 0,
#             "body": [[7, 7], [7, 8], [7, 9]],
#             "direction": "UP",
#             "alive": True,
#             "score": 100
#         },
#         ...
#     ],
#     "food_items": [
#         {"pos": [5, 5], "type": "worm"},
#         {"pos": [10, 10], "type": "apple"}
#     ],
#     "frame": 12345
# }
#
# GAME_START (Host -> Clients):
# {
#     "type": "game_start",
#     "num_players": 3,
#     "level_data": {...}  # Optional: level walls, etc.
# }
#
# GAME_END (Host -> Clients):
# {
#     "type": "game_end",
#     "winner": 2,  # player_id of winner
#     "scores": [100, 200, 150]
# }
#
# PLAYER_ASSIGNED (Host -> Client):
# {
#     "type": "player_assigned",
#     "player_id": 1,  # This client controls player 1
#     "player_slot": 1
# }

def create_input_message(player_id, direction):
    """Create an input message from client to host"""
    return {
        "type": MessageType.INPUT.value,
        "player_id": player_id,
        "direction": direction
    }

def create_game_state_message(snakes, food_items, frame):
    """Create a game state message from host to clients"""
    snake_data = []
    for snake in snakes:
        snake_data.append({
            "player_id": snake.player_id,
            "body": snake.body.copy(),
            "direction": snake.direction.name,
            "alive": snake.alive,
            "lives": snake.lives if hasattr(snake, 'lives') else 3
        })
    
    food_data = []
    for pos, food_type in food_items:
        food_data.append({
            "pos": list(pos),
            "type": food_type
        })
    
    return {
        "type": MessageType.GAME_STATE.value,
        "snakes": snake_data,
        "food_items": food_data,
        "frame": frame
    }

def create_game_start_message(num_players):
    """Create a game start message from host to clients"""
    return {
        "type": MessageType.GAME_START.value,
        "num_players": num_players
    }

def create_game_end_message(winner_id, final_scores):
    """Create a game end message from host to clients"""
    return {
        "type": MessageType.GAME_END.value,
        "winner": winner_id,
        "scores": final_scores
    }

def create_player_assigned_message(player_id, player_slot):
    """Create a player assignment message from host to client"""
    return {
        "type": MessageType.PLAYER_ASSIGNED.value,
        "player_id": player_id,
        "player_slot": player_slot
    }
