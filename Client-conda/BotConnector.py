from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo
from game_viewer_files.main_viewer import Viewer
from bot import Bot
import pygame
import game_viewer_files.config as c
import time
import subprocess


class BotConnector:
    def __init__(self, cmd: str):
        self.cmd = cmd
    def start_bot(self, inp: str):
        bot_process = subprocess.run(args=self.cmd,stdout=subprocess.PIPE, input=inp, encoding="ascii")
        return bot_process.stdout
