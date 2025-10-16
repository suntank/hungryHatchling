import pygame
from game_core import *

def draw_high_scores(screen, font_small, font_medium, font_large, high_scores):
    """Draw high scores screen"""
    screen.fill(BLACK)
    
    title = font_large.render("HIGH SCORES", True, YELLOW)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
    screen.blit(title, title_rect)
    
    if not high_scores:
        no_scores = font_medium.render("No scores yet!", True, WHITE)
        no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(no_scores, no_scores_rect)
    else:
        for i, entry in enumerate(high_scores[:10]):
            name = entry['name']
            score = entry['score']
            y = 100 + i * 36
            
            rank_text = font_small.render("{}.".format(i+1), True, WHITE)
            screen.blit(rank_text, (40, y))
            
            name_text = font_small.render(name, True, GREEN)
            screen.blit(name_text, (90, y))
            
            score_text = font_small.render(str(score), True, YELLOW)
            score_rect = score_text.get_rect(right=SCREEN_WIDTH - 40, top=y)
            screen.blit(score_text, score_rect)
    
    hint_text = font_small.render("Start to continue", True, WHITE)
    hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 440))
    screen.blit(hint_text, hint_rect)
