import pygame


class Snake:
    def __init__(self, body_pieces, is_snake_alive, name):
        self.body_pieces = body_pieces
        self.alive = is_snake_alive
        self.name = name

    def get_alive_status(self):
        return self.alive

    def get_color(self):
        return self.body_pieces[0].get_color()

    def get_name(self):
        return self.name

    def draw(self, surface):
        if len(self.body_pieces) <= 0:
            return
        if len(self.body_pieces) == 1:
            self.body_pieces[0].draw(surface, self.alive)
            return
        # drawing head
        head = self.body_pieces[0]
        neck = self.body_pieces[1]
        if head.left == neck.left:
            if head.top > neck.top:  # neck is higher than head, but coordinates differ
                pygame.draw.polygon(surface, head.get_color(),
                                    [(head.left + (head.width / 2), head.top + (head.width / 2)),
                                    (head.left + 1, head.top + 1),
                                    (head.right - 1, head.top + 1)])
                if self.alive is False:
                    pygame.draw.polygon(surface, (0, 0, 0),
                                        [(head.left + (head.width / 2), head.top + (head.width / 2) - 2),
                                         (head.left + 2, head.top + 1),
                                         (head.right - 2, head.top + 1)])
            else:  # neck is lower than head, but coordinates differ
                pygame.draw.polygon(surface, head.get_color(),
                                    [(head.left + (head.width / 2), head.top + (head.width / 2)),
                                    (head.left + 1, head.bottom - 1),
                                    (head.right - 1, head.bottom - 1)])
                if self.alive is False:
                    pygame.draw.polygon(surface, (0, 0, 0),
                                        [(head.left + (head.width / 2), head.top + (head.width / 2) + 2),
                                         (head.left + 2, head.bottom - 1),
                                         (head.right - 2, head.bottom - 1)])
        else:
            if head.left < neck.left:  # head is to the left of the neck
                pygame.draw.polygon(surface, head.get_color(),
                                    [(head.left + (head.width / 2), head.top + (head.width / 2)),
                                     (head.right - 1, head.top + 1),
                                     (head.right - 1, head.bottom - 1)])
                if self.alive is False:
                    pygame.draw.polygon(surface, (0, 0, 0),
                                        [(head.left + (head.width / 2) + 2, head.top + (head.width / 2)),
                                         (head.right - 1, head.top + 2),
                                         (head.right - 1, head.bottom - 2)])
            else:  # head is to the right of the neck
                pygame.draw.polygon(surface, head.get_color(),
                                    [(head.left + (head.width / 2), head.top + (head.width / 2)),
                                     (head.left + 1, head.top + 1),
                                     (head.left + 1, head.bottom - 1)])
                if self.alive is False:
                    pygame.draw.polygon(surface, (0, 0, 0),
                                        [(head.left + (head.width / 2) - 2, head.top + (head.width / 2)),
                                         (head.left + 1, head.top + 2),
                                         (head.left + 1, head.bottom - 2)])
        for i in self.body_pieces[1:]:
            i.draw(surface, self.alive)
