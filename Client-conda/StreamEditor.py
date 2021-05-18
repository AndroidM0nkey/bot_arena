from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo
from game_viewer_files.main_viewer import get_message_and_display
from bot import Bot
from BotConnector import BotConnector
import pygame
import game_viewer_files.config as c
import time
import subprocess


class StreamEditor:
    inf = 1000000000

    def __init__(self, snake_name:str, cmd:str):
        self.snake_name = snake_name
        self.cmd = cmd

    def get_snake_index(self, field_state: FieldState):
        ind = 2
        for snake_names in field_state.snakes.keys():
            if snake_names == self.snake_name:
                return ind
            ind += 2 

    def field_to_matrix(self, f_height, f_width, field_state: FieldState):

        matrix = [[0 for i in range(f_height)] for j in range(f_width)]
        snake_index = 2

        for snake_state in field_state.snakes.values():
            
            x = snake_state.head.x
            y = snake_state.head.y
            matrix[y][x] = snake_index + 1

            for snake_cell in snake_state.tail:
                if snake_cell == Direction.UP():
                    y += 1
                if snake_cell == Direction.DOWN():
                    y -= 1
                if snake_cell == Direction.LEFT():
                    x -= 1
                if snake_cell == Direction.RIGHT():
                    x += 1
                matrix[y][x] = snake_index
            
            snake_index += 2

        return matrix

    def matrix_into_str(self, f_height, f_width, matrix, field_state: FieldState):
        str_out = ""
        n = f_width.to_string()
        m = f_height.to_string()
        ind = (self.get_snake_index(self, field_state)).to_string()
        ind_head = (self.get_snake_index(self, field_state) + 1).to_string()
        str_out+=m
        str_out+=" "
        str_out+=n
        str_out+=" "
        str_out+=ind
        str_out+=" "
        str_out+=ind_head
        str_out+=" "
        for i in matrix:
            for j in i:
                str_out+=j.to_string()
                str_out+=" "
        str_out+="\n"
        return str_out

    def make_str(self, f_height, f_width, field_state: FieldState):
        matrix = self.field_to_matrix(self, f_height, f_width, field_state)
        str_out = self.matrix_into_str(self, f_height, f_width, matrix, field_state)
        return str_out

    def call_bot(self, f_height, f_width, field_state: FieldState):
        cur_bot = BotConnector(self.cmd)
        inp = self.make_str(self, f_height, f_width, field_state)
        return cur_bot.start_bot(inp)



