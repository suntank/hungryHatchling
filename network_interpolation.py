"""
Network Interpolation and Lag Compensation Module

Implements advanced networking techniques for smooth multiplayer gameplay:
- State buffering for jitter smoothing
- Client-side prediction (dead reckoning) for snakes
- Interpolation between received states
- Extrapolation for delayed packets
"""

import time
from collections import deque
from game_core import Direction, GRID_WIDTH, GRID_HEIGHT


class StateBuffer:
    """
    Circular buffer that stores recent game states for interpolation.
    Allows smooth playback by rendering slightly behind real-time.
    """
    
    def __init__(self, buffer_time_ms=100, max_states=30):
        """
        Args:
            buffer_time_ms: How far behind real-time to render (in milliseconds)
            max_states: Maximum number of states to keep in buffer
        """
        self.buffer_time = buffer_time_ms / 1000.0  # Convert to seconds
        self.max_states = max_states
        self.states = deque(maxlen=max_states)
        self.last_receive_time = 0
        self.estimated_server_tick_rate = 1/60.0  # Assume 60 updates/sec initially
        
    def add_state(self, state, frame_number):
        """Add a new state to the buffer with timestamp"""
        current_time = time.time()
        
        # Estimate server tick rate from frame differences
        if self.states and frame_number > 0:
            last_state = self.states[-1]
            if last_state['frame'] > 0:
                frame_diff = frame_number - last_state['frame']
                time_diff = current_time - last_state['receive_time']
                if frame_diff > 0 and time_diff > 0:
                    # Smooth the tick rate estimate
                    new_estimate = time_diff / frame_diff
                    self.estimated_server_tick_rate = (
                        0.9 * self.estimated_server_tick_rate + 
                        0.1 * new_estimate
                    )
        
        self.states.append({
            'state': state,
            'frame': frame_number,
            'receive_time': current_time
        })
        self.last_receive_time = current_time
        
    def get_interpolated_state(self):
        """
        Get interpolated state between two buffered states.
        Returns tuple: (state_before, state_after, interpolation_factor)
        Returns None if not enough states buffered.
        """
        if len(self.states) < 2:
            # Not enough states - return latest if available
            if self.states:
                return self.states[-1]['state'], None, 0.0
            return None, None, 0.0
        
        # Calculate render time (slightly behind real-time)
        render_time = time.time() - self.buffer_time
        
        # Find the two states to interpolate between
        state_before = None
        state_after = None
        
        for i in range(len(self.states) - 1):
            if (self.states[i]['receive_time'] <= render_time <= 
                self.states[i + 1]['receive_time']):
                state_before = self.states[i]
                state_after = self.states[i + 1]
                break
        
        # If render_time is before all states, use oldest
        if state_before is None and render_time < self.states[0]['receive_time']:
            return self.states[0]['state'], None, 0.0
        
        # If render_time is after all states, extrapolate from latest
        if state_before is None:
            state_before = self.states[-2]
            state_after = self.states[-1]
            # Calculate how far we need to extrapolate
            time_since_last = time.time() - state_after['receive_time']
            if time_since_last > 0.5:  # Don't extrapolate more than 500ms
                return state_after['state'], None, 0.0
            # Return extrapolation info
            return state_before['state'], state_after['state'], 1.0 + (
                time_since_last / max(0.001, 
                    state_after['receive_time'] - state_before['receive_time'])
            )
        
        # Calculate interpolation factor (0.0 to 1.0)
        time_range = state_after['receive_time'] - state_before['receive_time']
        if time_range <= 0:
            return state_after['state'], None, 0.0
            
        factor = (render_time - state_before['receive_time']) / time_range
        factor = max(0.0, min(1.0, factor))
        
        return state_before['state'], state_after['state'], factor
    
    def get_latest_state(self):
        """Get the most recent state without interpolation"""
        if self.states:
            return self.states[-1]['state']
        return None
    
    def clear(self):
        """Clear all buffered states"""
        self.states.clear()
        
    def time_since_last_update(self):
        """Get time since last state was received"""
        if self.last_receive_time == 0:
            return float('inf')
        return time.time() - self.last_receive_time


class SnakePredictor:
    """
    Client-side prediction for snake movement.
    Predicts snake positions based on direction and speed when
    network updates are delayed.
    """
    
    def __init__(self):
        self.predictions = {}  # player_id -> prediction data
        
    def update_from_server(self, player_id, body, direction, alive, frame):
        """Update prediction state with authoritative server data"""
        self.predictions[player_id] = {
            'body': [tuple(pos) for pos in body],
            'direction': direction,
            'alive': alive,
            'last_server_frame': frame,
            'last_update_time': time.time(),
            'predicted_moves': 0
        }
        
    def predict_position(self, player_id, move_interval_frames, frames_ahead=1):
        """
        Predict snake position ahead of last known state.
        
        Args:
            player_id: Which snake to predict
            move_interval_frames: How many frames between moves
            frames_ahead: How many frames to predict ahead
            
        Returns:
            Predicted body positions or None if no prediction available
        """
        if player_id not in self.predictions:
            return None
            
        pred = self.predictions[player_id]
        if not pred['alive'] or not pred['body']:
            return None
            
        # Calculate how many moves should have happened
        time_since_update = time.time() - pred['last_update_time']
        expected_moves = int(time_since_update * 60 / move_interval_frames)
        
        # Limit prediction to avoid runaway
        max_prediction_moves = 5
        moves_to_predict = min(expected_moves - pred['predicted_moves'], 
                               max_prediction_moves)
        
        if moves_to_predict <= 0:
            return pred['body']
            
        # Predict movement
        predicted_body = list(pred['body'])
        direction = pred['direction']
        
        for _ in range(moves_to_predict):
            head = predicted_body[0]
            
            # Calculate new head position based on direction
            if direction == Direction.UP:
                new_head = (head[0], (head[1] - 1) % GRID_HEIGHT)
            elif direction == Direction.DOWN:
                new_head = (head[0], (head[1] + 1) % GRID_HEIGHT)
            elif direction == Direction.LEFT:
                new_head = ((head[0] - 1) % GRID_WIDTH, head[1])
            elif direction == Direction.RIGHT:
                new_head = ((head[0] + 1) % GRID_WIDTH, head[1])
            else:
                new_head = head
                
            # Move snake (insert new head, remove tail)
            predicted_body = [new_head] + predicted_body[:-1]
            
        pred['predicted_moves'] = expected_moves
        return predicted_body
    
    def clear(self):
        """Clear all predictions"""
        self.predictions.clear()


def interpolate_snake_body(body_before, body_after, factor):
    """
    Interpolate between two snake body states.
    
    Args:
        body_before: List of (x, y) positions before
        body_after: List of (x, y) positions after
        factor: Interpolation factor (0.0 = before, 1.0 = after, >1.0 = extrapolate)
        
    Returns:
        List of interpolated (x, y) float positions
    """
    if not body_before:
        return body_after if body_after else []
    if not body_after:
        return body_before
        
    result = []
    
    # Interpolate each segment
    for i in range(max(len(body_before), len(body_after))):
        if i < len(body_before) and i < len(body_after):
            pos_before = body_before[i]
            pos_after = body_after[i]
            
            # Handle wrapping (if positions are far apart, snake wrapped)
            dx = pos_after[0] - pos_before[0]
            dy = pos_after[1] - pos_before[1]
            
            # Adjust for screen wrapping
            if abs(dx) > GRID_WIDTH // 2:
                if dx > 0:
                    pos_before = (pos_before[0] + GRID_WIDTH, pos_before[1])
                else:
                    pos_after = (pos_after[0] + GRID_WIDTH, pos_after[1])
                    
            if abs(dy) > GRID_HEIGHT // 2:
                if dy > 0:
                    pos_before = (pos_before[0], pos_before[1] + GRID_HEIGHT)
                else:
                    pos_after = (pos_after[0], pos_after[1] + GRID_HEIGHT)
            
            # Linear interpolation (or extrapolation if factor > 1)
            interp_x = pos_before[0] + (pos_after[0] - pos_before[0]) * factor
            interp_y = pos_before[1] + (pos_after[1] - pos_before[1]) * factor
            
            # Wrap back to grid bounds
            interp_x = interp_x % GRID_WIDTH
            interp_y = interp_y % GRID_HEIGHT
            
            result.append((interp_x, interp_y))
        elif i < len(body_after):
            # New segment in after state
            result.append(body_after[i])
        else:
            # Segment only in before state (snake shrunk)
            if factor < 0.5:
                result.append(body_before[i])
                
    return result


class NetworkInterpolator:
    """
    Main class that coordinates all lag compensation techniques.
    Use this in the game client to get smooth snake positions.
    """
    
    def __init__(self, buffer_time_ms=80):
        """
        Args:
            buffer_time_ms: Render delay for interpolation (higher = smoother but more latency)
        """
        self.state_buffer = StateBuffer(buffer_time_ms=buffer_time_ms)
        self.predictor = SnakePredictor()
        self.enabled = True
        self.last_frame = -1
        
        # Stats for debugging
        self.interpolation_count = 0
        self.extrapolation_count = 0
        self.prediction_count = 0
        
    def add_server_state(self, snakes_data, frame_number):
        """
        Add a new server state update.
        
        Args:
            snakes_data: List of snake data dicts from server
            frame_number: Server frame number
        """
        if frame_number <= self.last_frame:
            return  # Old/duplicate state, ignore
            
        self.last_frame = frame_number
        
        # Add to state buffer
        self.state_buffer.add_state({
            'snakes': snakes_data,
            'frame': frame_number
        }, frame_number)
        
        # Update predictor with latest data
        for snake_data in snakes_data:
            player_id = snake_data.get('player_id', 0)
            body = snake_data.get('body', [])
            direction_str = snake_data.get('direction', 'RIGHT')
            try:
                direction = Direction[direction_str]
            except:
                direction = Direction.RIGHT
            alive = snake_data.get('alive', True)
            
            self.predictor.update_from_server(player_id, body, direction, alive, frame_number)
    
    def get_snake_positions(self, player_id, move_interval=16):
        """
        Get smoothed snake positions for rendering.
        
        Args:
            player_id: Which snake to get positions for
            move_interval: Frames between snake moves (for prediction speed)
            
        Returns:
            List of (x, y) float positions for smooth rendering,
            or None if no data available
        """
        if not self.enabled:
            # Fallback to latest state
            state = self.state_buffer.get_latest_state()
            if state:
                for snake in state.get('snakes', []):
                    if snake.get('player_id') == player_id:
                        return snake.get('body', [])
            return None
        
        # Try interpolation first
        state_before, state_after, factor = self.state_buffer.get_interpolated_state()
        
        if state_before is None:
            # No states available, try prediction
            predicted = self.predictor.predict_position(player_id, move_interval)
            if predicted:
                self.prediction_count += 1
            return predicted
        
        # Find snake data in states
        body_before = None
        body_after = None
        
        for snake in state_before.get('snakes', []):
            if snake.get('player_id') == player_id:
                body_before = [tuple(pos) for pos in snake.get('body', [])]
                break
                
        if state_after:
            for snake in state_after.get('snakes', []):
                if snake.get('player_id') == player_id:
                    body_after = [tuple(pos) for pos in snake.get('body', [])]
                    break
        
        if body_before is None:
            return None
            
        if body_after is None or factor == 0.0:
            # Only one state, return it directly
            return body_before
            
        # Interpolate or extrapolate
        if factor > 1.0:
            self.extrapolation_count += 1
            # Limit extrapolation factor
            factor = min(factor, 1.5)
        else:
            self.interpolation_count += 1
            
        return interpolate_snake_body(body_before, body_after, factor)
    
    def get_snake_direction(self, player_id):
        """Get the latest known direction for a snake"""
        state = self.state_buffer.get_latest_state()
        if state:
            for snake in state.get('snakes', []):
                if snake.get('player_id') == player_id:
                    return snake.get('direction', 'RIGHT')
        return 'RIGHT'
    
    def get_snake_alive(self, player_id):
        """Get the latest known alive status for a snake"""
        state = self.state_buffer.get_latest_state()
        if state:
            for snake in state.get('snakes', []):
                if snake.get('player_id') == player_id:
                    return snake.get('alive', True)
        return True
    
    def get_snake_lives(self, player_id):
        """Get the latest known lives for a snake"""
        state = self.state_buffer.get_latest_state()
        if state:
            for snake in state.get('snakes', []):
                if snake.get('player_id') == player_id:
                    return snake.get('lives', 3)
        return 3
    
    def is_stale(self, max_stale_time=0.5):
        """Check if we haven't received updates in a while"""
        return self.state_buffer.time_since_last_update() > max_stale_time
    
    def reset(self):
        """Reset all state (e.g., when starting a new game)"""
        self.state_buffer.clear()
        self.predictor.clear()
        self.last_frame = -1
        self.interpolation_count = 0
        self.extrapolation_count = 0
        self.prediction_count = 0
        
    def get_stats(self):
        """Get interpolation statistics for debugging"""
        return {
            'interpolations': self.interpolation_count,
            'extrapolations': self.extrapolation_count,
            'predictions': self.prediction_count,
            'buffer_size': len(self.state_buffer.states),
            'time_since_update': self.state_buffer.time_since_last_update()
        }
