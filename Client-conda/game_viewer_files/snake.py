import pygame


class Snake:
    def __init__(self, body_pieces):
        self.body_pieces = body_pieces

    def draw(self, surface):
        if len(self.body_pieces) <= 0:
            return
        if len(self.body_pieces) == 1:
            self.body_pieces[0].draw(surface)
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
            else:  # neck is lower than head, but coordinates differ
                pygame.draw.polygon(surface, head.get_color(),
                                    [(head.left + (head.width / 2), head.top + (head.width / 2)),
                                    (head.left + 1, head.bottom - 1),
                                    (head.right - 1, head.bottom - 1)])
        else:
            if head.left < neck.left:  # head is to the left of the neck
                pygame.draw.polygon(surface, head.get_color(),
                                    [(head.left + (head.width / 2), head.top + (head.width / 2)),
                                     (head.right - 1, head.top + 1),
                                     (head.right - 1, head.bottom - 1)])
            else:  # head is to the right of the neck
                pygame.draw.polygon(surface, head.get_color(),
                                    [(head.left + (head.width / 2), head.top + (head.width / 2)),
                                     (head.left + 1, head.top + 1),
                                     (head.left + 1, head.bottom - 1)])
        for i in self.body_pieces[1:]:
            i.draw(surface)
