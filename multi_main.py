import pygame
from random import randint, random, choice
import sys
import socket, time, threading

pygame.init()

size = width, height = 1280, 720
screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
building_group = pygame.sprite.Group()
settings_buttons_group = pygame.sprite.Group()
button_group = pygame.sprite.Group()
terrain_group = pygame.sprite.Group()
background_group = pygame.sprite.Group()

bank_buttons = pygame.sprite.Group()

pharm_buttons = pygame.sprite.Group()
pharm_group = pygame.sprite.Group()
background_pharm = pygame.sprite.Group()
pharm_products = pygame.sprite.Group()

shop_buttons = pygame.sprite.Group()
shop_group = pygame.sprite.Group()
background_shop = pygame.sprite.Group()
shop_products = pygame.sprite.Group()

house_buttons = pygame.sprite.Group()
house_group = pygame.sprite.Group()
background_house = pygame.sprite.Group()
house_products = pygame.sprite.Group()

product_buttons = pygame.sprite.Group()

remote_players = pygame.sprite.Group()
online_players = dict()

building_collide_step = 0
near_building_message = None
near_building = None
gravity = 1
menu_is_on = False
music_on = True
effects_on = True
global_exit = False

ip = socket.gethostbyname('0.tcp.ngrok.io')
host = ip
# host = '127.0.0.1'
port = 19514

caught_ids = []

speeches = {'intro': pygame.mixer.Sound('data/speech/intro.wav'),
            '1': pygame.mixer.Sound('data/speech/1.wav'),
            '2': pygame.mixer.Sound('data/speech/2.wav'),
            '3': pygame.mixer.Sound('data/speech/3.wav'),
            'autro': pygame.mixer.Sound('data/speech/autro.wav'),
            'news': pygame.mixer.Sound('data/speech/news.wav')}

music = {'main': pygame.mixer.Sound('data/music/main_music.ogg')}
music['main'].play(-1)

player_params = dict()
products = dict()


def operate_player_data():
    global global_exit
    while True:
        try:
            con = socket.socket()
            try:
                con.connect((host, port))
            except ConnectionRefusedError:
                return

            con.send((player.id + r'\t' + player.get_pos_info() + r'\t' + '%'.join(caught_ids)).encode('utf-8'))

            end = False
            while not end:
                data = con.recv(1024).decode('utf-8')
                if 'end' in data and len(data) > 3:
                    end = True
                    data = data[:data.index('end')]
                elif data == 'end':
                    break
                id, params = data.split(r'\t')[0], r'\t'.join(data.split(r'\t')[1:])
                if str(id) not in player_params.keys() and id != player.id:
                    role = params.split(r'\t')[0]
                    player_params[id] = RemotePlayer(str(id), 0, 0, role, remote_players)
                    if len(remote_players.sprites()) == 0:
                        player_params[id] = RemotePlayer(str(id), 0, 0, role, remote_players)
                    time.sleep(0.002)
                player_params[id].set_params(params)
                time.sleep(0.002)
        finally:
            con.close()
        if global_exit:
            break


def stop_speeches():
    for sound in speeches.values():
        sound.stop()


def load_image(path, colorkey=None, size=None) -> pygame.Surface:
    image = pygame.image.load(path).convert_alpha()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    if size:
        image = pygame.transform.scale(image, size)
    return image


def check_collisions(player):
    check_near_building(player)
    for i in all_sprites:
        if id(player) == id(i):
            continue
        if i.is_obstacle():
            if pygame.sprite.collide_mask(player, i):
                return True
    return False


def check_near_building(player):
    global near_building, near_building_message
    near_building, near_building_message = None, None
    for building in building_group:
        if pygame.sprite.collide_mask(player, building):
            near_building = building
            near_building_message = f'Нажмите [E], чтобы войти в {building.name}'


def render_text(line, size=50, color=(255, 255, 255)):
    font = pygame.font.Font(None, size)
    text = font.render(line, 1, color)
    return text


class RemotePlayer(pygame.sprite.Sprite):
    def __init__(self, id, x, y, role, *groups):
        self.id = id
        super().__init__(groups)
        self.role = role
        self.scanner_is_on = False
        self.side = 'left'
        self.update_images()

        self.image = self.frames['right'][0]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

        self.is_moving = False
        self.clock = pygame.time.Clock()

        self.infected = None

        self.caught = 0

    def get_coords(self):
        return self.rect.x, self.rect.y

    def set_position(self, pos):
        self.rect.x, self.rect.y = pos

    def set_moving(self, value):
        self.is_moving = value

    def is_obstacle(self):
        return False

    def set_params(self, data):
        data = data.split(r'\t')[1:]
        # print(123)
        # print(data)
        try:
            # assert len(data) == 5
            new_x, new_y = int(data[0]), int(data[1])
            moving = True if data[2] == 'True' else False
            assert data[3] in ['left', 'right'] and str(data[3]).isalpha()
            infected = str(data[4])
        except Exception as e:
            print('error', e)
            return
        self.set_position((new_x + terrain.rect.x, new_y + terrain.rect.y))
        self.is_moving = moving
        while True:
            try:
                self.image = self.frames[data[3]][0]
            except IndexError:
                continue
            break
        if internal_id in data[5].split('%'):
            screen.fill((0, 0, 0))
            # background_group.draw(screen)
            text = render_text('Вы арестованы за нарушение карантина!!!')
            screen.blit(text, (width // 2 - text.get_width() // 2, height // 2))
            pygame.display.flip()
            for i in range(5):
                self.clock.tick(1)

            exit_game()
        if infected == 'None':
            self.infected = None
        elif infected.isdigit():
            self.infected = int(infected)
        else:
            print('[ERROR] value infection:', infected)

    def update_images(self):
        if not self.role:
            self.kill()
        self.frames = {'left': [], 'right': []}
        self.frames['left'].append(
            pygame.transform.flip(load_image(f'data/characters/{self.role}_right_5.png', size=(80, 110)), 1, 0))
        if self.scanner_is_on:
            if self.infected == 1:
                self.frames['left'][0].blit(load_image('data/characters/not_stated.png', size=(20, 20)), (60, 0))
            elif self.infected == 2:
                self.frames['left'][0].blit(load_image('data/characters/ok.png', size=(20, 20)), (60, 0))
            elif self.infected == 3:
                self.frames['left'][0].blit(load_image('data/characters/infected.png', size=(20, 20)), (60, 0))

        self.frames['right'].append(
            load_image(f'data/characters/{self.role}_right_5.png', size=(80, 110)))
        if self.scanner_is_on:
            if self.infected == 1:
                self.frames['right'][0].blit(load_image('data/characters/not_stated.png', size=(20, 20)), (60, 0))
            elif self.infected == 2:
                self.frames['right'][0].blit(load_image('data/characters/ok.png', size=(20, 20)), (60, 0))
            elif self.infected == 3:
                self.frames['right'][0].blit(load_image('data/characters/infected.png', size=(20, 20)), (60, 0))

        self.image = self.frames[self.side][0]

    def update(self, *args):
        if not args:
            return
        scanner_on = args[0]
        if scanner_on != self.scanner_is_on:
            self.scanner_is_on = scanner_on
            self.update_images()


class Player(pygame.sprite.Sprite):
    speed = 10
    jump_power = 15
    infection_rate = 1500

    def __init__(self, x, y, role, *groups):
        super().__init__(groups)
        self.role = role
        self.inside = False

        self.frames = {'left': [], 'right': []}
        self.frames['left'].append(
            pygame.transform.flip(load_image(f'data/characters/{role}_right_5.png', size=(80, 110)), 1, 0))
        self.frames['right'].append(
            load_image(f'data/characters/{role}_right_5.png', size=(80, 110)))

        self.image = self.frames['right'][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

        self.prev_coords = x, y
        self.is_moving = False
        self.grav = 0
        self.is_jumping = False
        self.clock = pygame.time.Clock()
        self.side = 'left'

        self.health = 100
        self.hazard_risk = 0
        self.danger_level = 1
        self.hazard_timer = 0
        self.id = None

        self.card_money = 0
        self.cash = 5000

        self.objects = []
        pin = str(randint(1000, 9999))
        products['card'].description = (r'Пин код:\n' + str(pin)).split(r'\n')
        products['card'].pin = pin
        self.objects.append(products['card'])

        self.infected = 1 if self.role == 'citizen' else None

    def get_objects(self):
        return self.objects

    def add_objects(self, *objects):
        for i in objects:
            self.objects.append(i)

    def get_cash(self):
        return self.cash

    def set_cash(self, value):
        self.cash = value

    def give_money(self, amount):
        if amount <= self.cash:
            self.cash -= amount
            return True
        return False

    def set_card_money(self, value):
        self.card_money = value

    def get_card_money(self):
        return self.card_money

    def spend_money(self, amount):
        if amount <= self.card_money:
            self.card_money -= amount
            return True
        return False

    def set_position(self, pos):
        self.rect.x, self.rect.y = pos

    def set_moving(self, value):
        self.is_moving = value

    def get_coords(self):
        return self.rect.x, self.rect.y

    def get_card_balance(self):
        return self.card_money

    def is_obstacle(self):
        return False

    def move_left(self):
        self.side = 'left'
        self.image = self.frames[self.side][0]

        self.prev_coords = self.get_coords()
        self.rect.x -= Player.speed
        if check_collisions(self):
            self.rect.y -= 5
        if check_collisions(self):
            self.rect.y -= 10
        if check_collisions(self):
            self.rect.y -= 15
        if check_collisions(self):
            self.rect.x = self.prev_coords[0]
            self.rect.y = self.prev_coords[1]

    def move_right(self):
        self.side = 'right'
        self.image = self.frames[self.side][0]
        self.rect.x += Player.speed
        if check_collisions(self):
            self.rect.y -= 5
        if check_collisions(self):
            self.rect.y -= 10
        if check_collisions(self):
            self.rect.y -= 15
        if check_collisions(self):
            self.rect.x = self.prev_coords[0]
            self.rect.y = self.prev_coords[1]

    def move_down(self, value):
        self.prev_coords = self.get_coords()
        self.rect.y -= value
        if check_collisions(self):
            if self.grav < -20:
                self.health -= abs(self.grav) - 10
            self.rect.x = self.prev_coords[0]
            self.rect.y = self.prev_coords[1]
            self.grav = -5
            self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.grav = Player.jump_power
            self.is_jumping = True

    def render_info(self, color=(255, 255, 255), background=(0, 0, 0)):
        canvas = pygame.Surface((width // 2 + 175, 20))
        canvas.fill(background)
        font = pygame.font.Font(None, 30)
        canvas.blit(
            font.render(
                f'Здоровье: {self.health}%   Риск заражения: {self.hazard_risk}%   Наличные: {self.cash} Р     На карте: {self.card_money} Р',
                1, color), (0, 0))
        return canvas

    def get_pos_info(self):
        x, y = str(self.rect.x - terrain.rect.x), str(self.rect.y - terrain.rect.y)
        if self.inside:
            x, y = '0', '0'
        res = self.role + r'\t' + x + r'\t' + y + r'\t' + str(
            self.is_moving) + r'\t' + self.side + r'\t' + str(self.infected)
        # print(res)
        return res

    def update_params(self):
        if self.role == 'citizen':
            self.danger_level = 1 - (100 - self.health) / 100
            self.hazard_timer += self.clock.tick()
            if self.hazard_timer > Player.infection_rate * self.danger_level:
                self.hazard_risk += 1
                self.hazard_timer = 0

        if self.health <= 0:
            self.health = 0
        if self.hazard_risk >= 100:
            self.hazard_risk = 100

        if self.health == 0 or self.grav < -50:
            screen.fill((0, 0, 0))
            # background_group.draw(screen)
            screen.blit(self.render_info(), (0, 0))
            text = render_text('Вы мертвы!!!')
            screen.blit(text, (width // 2 - text.get_width() // 2, height // 2))
            pygame.display.flip()
            for i in range(5):
                self.clock.tick(1)

            exit_game()
        elif self.hazard_risk == 100:
            self.infected = 3

    def update(self, *args):
        self.move_down(self.grav)
        self.grav -= gravity

        self.update_params()


class Terrain(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(groups)
        self.image = load_image('data/textures/city_platforms.png')
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def is_obstacle(self):
        return True


class Bank(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(groups)
        self.image = load_image('data/buildings/bank.png', size=(250, 150))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)

        self.name = 'Банк'

    def is_obstacle(self):
        return False

    def enter(self):
        button_group.empty()
        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)
        running = True

        mode = ''
        right_pin = products['card'].pin
        current_pin = ''
        deposit_summ = ''

        main_display = pygame.Surface((width // 2, height // 3 + 150))
        main_display.fill((0, 0, 0))

        card_size = (100, 150)
        card = Button(width - card_size[0], height - card_size[1], *card_size,
                      load_image('data/objects/bank_card.png', size=card_size), None, 'card', bank_buttons)
        card_moving = False
        hole_rect = pygame.Rect(888, 107, 300, 20)

        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
               100, 50, images['exit_sign'], lambda: False, None, bank_buttons)

        Button(50, 100, 50, 50, images['right_arrow'], None, 'first', bank_buttons)
        Button(50, 200, 50, 50, images['right_arrow'], None, 'second', bank_buttons)
        Button(50, 300, 50, 50, images['right_arrow'], None, 'third', bank_buttons)

        Button(100 + main_display.get_width(), 100, 50, 50, images['left_arrow'], None, 'fourth', bank_buttons)
        Button(100 + main_display.get_width(), 200, 50, 50, images['left_arrow'], None, 'fifth', bank_buttons)
        Button(100 + main_display.get_width(), 300, 50, 50, images['left_arrow'], None, 'sixth', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('1', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4, 470, 50, 50, image, None, '1', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('2', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 470, 50, 50, image, None, '2', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('3', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 2, 470, 50, 50, image, None, '3', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('4', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4, 545, 50, 50, image, None, '4', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('5', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 545, 50, 50, image, None, '5', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('6', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 2, 545, 50, 50, image, None, '6', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('7', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4, 620, 50, 50, image, None, '7', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('8', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 620, 50, 50, image, None, '8', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('9', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 2, 620, 50, 50, image, None, '9', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('0', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 670, 50, 50, image, None, '0', bank_buttons)

        image = load_image('data/objects/long_button.png')
        image.blit(render_text('Enter', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 3, 620, 208, 47, image, None, 'enter', bank_buttons)

        image = load_image('data/objects/long_button.png')
        image.blit(render_text('Clear', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 3, 545, 208, 47, image, None, 'clear', bank_buttons)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEMOTION:
                    if card_moving:
                        card.rect.x, card.rect.y = event.pos

                    if card.rect.colliderect(hole_rect):
                        mode = 'pin'
                        bank_buttons.remove(card)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in bank_buttons:
                        if btn.rect.collidepoint(event.pos):
                            if not btn.id:
                                running = btn.run()
                            elif btn.id == 'card':
                                card_moving = True
                                card.rect.x, card.rect.y = event.pos
                            elif btn.id == 'clear':
                                current_pin = ''
                                deposit_summ = ''
                            elif btn.id.isdigit() and mode == 'pin':
                                current_pin += btn.id
                                if len(current_pin) == 4 and current_pin == right_pin:
                                    mode = 'main'
                                    current_pin = ''
                            elif mode == 'main':
                                if btn.id == 'first':
                                    mode = 'balance'
                                elif btn.id == 'second':
                                    mode = 'deposit'
                            elif mode == 'balance':
                                if btn.id == 'sixth':
                                    mode = 'main'
                            elif mode == 'deposit':
                                if btn.id == 'enter':
                                    if deposit_summ.isdigit() and player.give_money(int(deposit_summ)):
                                        player.card_money += int(deposit_summ)
                                        mode = 'success'
                                    else:
                                        mode = 'error'
                                    deposit_summ = ''
                                elif btn.id.isdigit():
                                    deposit_summ += btn.id
                            elif mode == 'error' or mode == 'success':
                                mode = 'main'
                            button_group.empty()
                            pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, button_group)
            data = pygame.key.get_pressed()
            player.set_moving(False)
            if data[27]:
                menu(pause=True)
                button_group.empty()
                pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

            main_display.fill((0, 0, 0))
            if mode == 'pin':
                main_display.blit(render_text('Введите пин код:', color=(232, 208, 79)),
                                  (main_display.get_width() // 4, main_display.get_height() // 2 - 50))
                main_display.blit(render_text(('_' * (4 - len(current_pin))).rjust(4, '*'), color=(232, 208, 79)),
                                  (main_display.get_width() // 2, main_display.get_height() // 2))
            elif mode == 'main':
                main_display.blit(render_text('Показать баланс', color=(232, 208, 79)), (60, 30))
                main_display.blit(render_text('Внести наличные', color=(232, 208, 79)), (60, 130))
            elif mode == 'balance':
                main_display.blit(
                    render_text(f'Ваш баланс: {player.get_card_balance()} рублей', color=(232, 208, 79)),
                    (0, main_display.get_height() // 3))
                main_display.blit(render_text('Назад', color=(232, 208, 79)), (main_display.get_width() - 125, 250))
            elif mode == 'success':
                main_display.blit(render_text('Успешно!', color=(232, 208, 79)),
                                  (main_display.get_width() // 3, main_display.get_height() // 2))
            elif mode == 'error':
                main_display.blit(render_text('Ошибка!', color=(232, 208, 79)),
                                  (main_display.get_width() // 3, main_display.get_height() // 2))
            elif mode == 'deposit':
                main_display.blit(render_text('Введите сумму:', color=(232, 208, 79)),
                                  (main_display.get_width() // 4, main_display.get_height() // 2 - 50))
                main_display.blit(render_text(deposit_summ, color=(232, 208, 79)),
                                  (main_display.get_width() // 2, main_display.get_height() // 2))

            screen.fill((156, 65, 10))
            player.update_params()
            button_group.draw(screen)
            bank_buttons.draw(screen)
            screen.blit(player.render_info(background=(156, 65, 10)), (0, 0))
            screen.blit(main_display, (100, 70))
            pygame.draw.rect(screen, (0, 0, 0), hole_rect)
            pygame.display.flip()
            clock.tick(fps)
        bank_buttons.empty()
        button_group.empty()


class MainHouse(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(groups)
        self.image = load_image('data/buildings/main_house.png', size=(250, 500))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)

        self.name = 'Дом'

        self.clock = pygame.time.Clock()

    def is_obstacle(self):
        return False

    def enter(self):
        def play_radio_info():
            speeches['news'].play()
            return True

        button_group.empty()

        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, house_buttons)

        radio = Button(width - 350, height // 2 - 137, 170, 145, images['radio'], play_radio_info, None, house_buttons)

        backgr = pygame.sprite.Sprite(background_house)
        backgr.image = load_image('data/inside/room.png', size=size)
        backgr.rect = backgr.image.get_rect()

        running = True

        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
               100, 50, images['exit_sign'], lambda: False, None, house_buttons)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in house_buttons:
                        if btn.rect.collidepoint(event.pos):
                            running = btn.run()

            data = pygame.key.get_pressed()
            player.set_moving(False)
            if data[27]:
                menu(pause=True)
                button_group.empty()
                pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, house_buttons)
            screen.fill((177, 170, 142))
            background_house.draw(screen)
            button_group.draw(screen)
            house_buttons.draw(screen)
            house_group.draw(screen)
            screen.blit(player.render_info(background=(177, 170, 142)), (0, 0))
            pygame.display.flip()
            clock.tick(fps)
        house_buttons.empty()
        house_group.empty()


class Shop(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(groups)
        self.image = load_image('data/buildings/shop_1.png', size=(250, 200))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)

        self.name = 'Продуктовый магазин'

    def is_obstacle(self):
        return False

    def enter(self):
        def checkout():
            def buy():
                summ = sum([i.get_price() for i in cart])
                if player.spend_money(summ):
                    player.add_objects(*cart)
                    for i in cart:
                        i.buy()
                    return False, True, 'success'
                return False, True, 'error'

            running = True
            shop_buttons.empty()
            Button(width // 3, height - 100, 200, 50, render_text('Назад'), lambda: (False, True, 'ok'), None,
                   shop_buttons)
            Button(width // 3 * 2, height - 100, 200, 50, render_text('Купить'), buy, None, shop_buttons)

            Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
                   100, 50, images['exit_sign'], lambda: (False, False, 'ok'), None, shop_buttons)

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for btn in shop_buttons:
                            if btn.rect.collidepoint(event.pos):
                                running, run, status = btn.run()
                data = pygame.key.get_pressed()
                player.set_moving(False)
                if data[27]:
                    menu(pause=True)
                    button_group.empty()
                    pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

                screen.fill((156, 65, 10))
                shop_buttons.draw(screen)
                screen.blit(player.render_info(background=(156, 65, 10)), (0, 0))
                for num in range(len(cart)):
                    screen.blit(render_text(f'{num + 1} -- {cart[num].name} ------ {cart[num].get_price()}'),
                                (width // 2, height // 2 - 200 + 35 * num))
                pygame.display.flip()
                clock.tick(fps)
            shop_buttons.empty()
            return run, status

        button_group.empty()
        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, pharm_buttons)

        backgr = pygame.sprite.Sprite(background_shop)
        backgr.image = load_image('data/inside/shop_1_inside.png', size=size)
        backgr.rect = backgr.image.get_rect()

        running = True

        carrot = products['carrot']
        if carrot.can_be_bought():
            carrot.set_pos((350, 180))
            carrot.add_to_groups(shop_products)

        potato = products['potato']
        if potato.can_be_bought():
            potato.set_pos((550, 180))
            potato.add_to_groups(shop_products)

        apple = products['apple']
        if apple.can_be_bought():
            apple.set_pos((350, 300))
            apple.add_to_groups(shop_products)

        cart = []
        cart_rect = pygame.Rect(950, 300, 150, 450)

        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
               100, 50, images['exit_sign'], lambda: False, None, shop_buttons)
        status = 'ok'
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in shop_buttons:
                        if btn.rect.collidepoint(event.pos):
                            running = btn.run()
                    for product in shop_products:
                        if product.rect.collidepoint(event.pos):
                            cart.append(product)
                            for i in cart:
                                i.reset_groups()
                    if cart_rect.collidepoint(event.pos):
                        running, status = checkout()
                        if status == 'success':
                            cart = []
                        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
                               100, 50, images['exit_sign'], lambda: False, None, shop_buttons)
                        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, shop_buttons)

            data = pygame.key.get_pressed()
            player.set_moving(False)
            if data[27]:
                menu(pause=True)
                button_group.empty()
                pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

            screen.fill((156, 65, 10))
            player.update_params()
            background_shop.draw(screen)
            button_group.draw(screen)
            shop_buttons.draw(screen)
            shop_group.draw(screen)
            shop_products.draw(screen)
            if status == 'error':
                screen.blit(render_text('Недостаточно средств! Посетите банк!', color=(255, 0, 0)), (200, 100))
            screen.blit(player.render_info(background=(179, 185, 206)), (0, 0))
            pygame.display.flip()
            clock.tick(fps)
        shop_buttons.empty()
        shop_group.empty()
        shop_products.empty()


class SecondShop(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(groups)
        self.image = load_image('data/buildings/shop_2.png', size=(250, 200))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)

        self.name = 'Хозяйственный магазин'

    def is_obstacle(self):
        return False

    def enter(self):
        def checkout():
            def buy():
                summ = sum([i.get_price() for i in cart])
                if player.spend_money(summ):
                    player.add_objects(*cart)
                    for i in cart:
                        i.buy()
                    return False, True, 'success'
                return False, True, 'error'

            running = True
            shop_buttons.empty()
            Button(width // 3, height - 100, 200, 50, render_text('Назад'), lambda: (False, True, 'ok'), None,
                   shop_buttons)
            Button(width // 3 * 2, height - 100, 200, 50, render_text('Купить'), buy, None, shop_buttons)

            Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
                   100, 50, images['exit_sign'], lambda: (False, False, 'ok'), None, shop_buttons)

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for btn in shop_buttons:
                            if btn.rect.collidepoint(event.pos):
                                running, run, status = btn.run()
                data = pygame.key.get_pressed()
                player.set_moving(False)
                if data[27]:
                    menu(pause=True)
                    button_group.empty()
                    pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

                screen.fill((156, 65, 10))
                shop_buttons.draw(screen)
                screen.blit(player.render_info(background=(156, 65, 10)), (0, 0))
                for num in range(len(cart)):
                    screen.blit(render_text(f'{num + 1} -- {cart[num].name} ------ {cart[num].get_price()}'),
                                (width // 2, height // 2 - 200 + 35 * num))
                pygame.display.flip()
                clock.tick(fps)
            shop_buttons.empty()
            return run, status

        button_group.empty()
        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, pharm_buttons)

        backgr = pygame.sprite.Sprite(background_shop)
        backgr.image = load_image('data/inside/shop_2_inside.png', size=size)
        backgr.rect = backgr.image.get_rect()

        running = True

        soap = products['soap']
        if soap.can_be_bought():
            soap.set_pos((950, 180))
            soap.add_to_groups(shop_products)

        cart = []
        cart_rect = pygame.Rect(300, 327, 80, 200)

        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
               100, 50, images['exit_sign'], lambda: False, None, shop_buttons)
        status = 'ok'
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in shop_buttons:
                        if btn.rect.collidepoint(event.pos):
                            running = btn.run()
                    for product in shop_products:
                        if product.rect.collidepoint(event.pos):
                            cart.append(product)
                            for i in cart:
                                i.reset_groups()
                    if cart_rect.collidepoint(event.pos):
                        a = 1
                        running, status = checkout()
                        if status == 'success':
                            cart = []
                        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
                               100, 50, images['exit_sign'], lambda: False, None, shop_buttons)
                        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, shop_buttons)

            data = pygame.key.get_pressed()
            player.set_moving(False)
            if data[27]:
                menu(pause=True)
                button_group.empty()
                pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

            screen.fill((156, 65, 10))
            player.update_params()
            background_shop.draw(screen)
            button_group.draw(screen)
            shop_buttons.draw(screen)
            shop_group.draw(screen)
            shop_products.draw(screen)
            if status == 'error':
                screen.blit(render_text('Недостаточно средств! Посетите банк!', color=(255, 0, 0)), (200, 100))
            screen.blit(player.render_info(background=(179, 185, 206)), (0, 0))
            pygame.display.flip()
            clock.tick(fps)
        shop_buttons.empty()
        shop_group.empty()
        shop_products.empty()


class Pharmacy(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(groups)
        self.image = load_image('data/buildings/pharmacy.png', size=(250, 200))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)

        self.name = 'Аптека'

    def is_obstacle(self):
        return False

    def enter(self):
        def checkout():
            def buy():
                summ = sum([i.get_price() for i in cart])
                if player.spend_money(summ):
                    player.add_objects(*cart)
                    for i in cart:
                        i.buy()
                    return False, True, 'success'
                return False, True, 'error'

            running = True
            pharm_buttons.empty()
            Button(width // 3, height - 100, 200, 50, render_text('Назад'), lambda: (False, True, 'ok'), None,
                   pharm_buttons)
            Button(width // 3 * 2, height - 100, 200, 50, render_text('Купить'), buy, None, pharm_buttons)

            Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
                   100, 50, images['exit_sign'], lambda: (False, False, 'ok'), None, pharm_buttons)

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for btn in pharm_buttons:
                            if btn.rect.collidepoint(event.pos):
                                running, run, status = btn.run()
                data = pygame.key.get_pressed()
                player.set_moving(False)
                if data[27]:
                    menu(pause=True)
                    button_group.empty()
                    pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

                screen.fill((156, 65, 10))
                pharm_buttons.draw(screen)
                screen.blit(player.render_info(background=(156, 65, 10)), (0, 0))
                for num in range(len(cart)):
                    screen.blit(render_text(f'{num + 1} -- {cart[num].name} ------ {cart[num].get_price()}'),
                                (width // 2, height // 2 - 200 + 35 * num))
                pygame.display.flip()
                clock.tick(fps)
            pharm_buttons.empty()
            return run, status

        button_group.empty()
        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, pharm_buttons)

        backgr = pygame.sprite.Sprite(background_pharm)
        backgr.image = load_image('data/inside/pharmacy_inside.png', size=size)
        backgr.rect = backgr.image.get_rect()

        running = True

        bottle = products['alcohol']
        if bottle.can_be_bought():
            bottle.set_pos((350, 180))
            bottle.add_to_groups(pharm_products)

        mask = products['mask']
        if mask.can_be_bought():
            mask.set_pos((550, 180))
            mask.add_to_groups(pharm_products)

        pills = products['pills']
        if pills.can_be_bought():
            pills.set_pos((750, 180))
            pills.add_to_groups(pharm_products)

        cart = []
        cart_rect = pygame.Rect(950, 300, 150, 450)

        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
               100, 50, images['exit_sign'], lambda: False, None, pharm_buttons)
        status = 'ok'
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in pharm_buttons:
                        if btn.rect.collidepoint(event.pos):
                            running = btn.run()
                    for product in pharm_products:
                        if product.rect.collidepoint(event.pos):
                            cart.append(product)
                            for i in cart:
                                i.reset_groups()
                    if cart_rect.collidepoint(event.pos):
                        running, status = checkout()
                        if status == 'success':
                            cart = []
                        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
                               100, 50, images['exit_sign'], lambda: False, None, pharm_buttons)
                        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, pharm_buttons)

            data = pygame.key.get_pressed()
            player.set_moving(False)
            if data[27]:
                menu(pause=True)
                button_group.empty()
                pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

            screen.fill((156, 65, 10))
            player.update_params()
            background_pharm.draw(screen)
            button_group.draw(screen)
            pharm_buttons.draw(screen)
            pharm_group.draw(screen)
            pharm_products.draw(screen)
            if status == 'error':
                screen.blit(render_text('Недостаточно средств! Посетите банк!', color=(255, 0, 0)), (200, 100))
            screen.blit(player.render_info(background=(179, 185, 206)), (0, 0))
            pygame.display.flip()
            clock.tick(fps)
        pharm_buttons.empty()
        pharm_group.empty()


class Hospital(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(groups)
        self.image = load_image('data/buildings/hospital.png', size=(370, 340))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)

        self.name = 'Больница'

    def is_obstacle(self):
        return False

    def enter(self):
        button_group.empty()
        if player.role != 'citizen':
            return
        if player.infected != 1:
            return
        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)
        running = True

        mode = 'main'
        current_year = ''
        math = ''
        answer = ''
        right_answer = ''

        main_display = pygame.Surface((width // 2, height // 3 + 150))
        main_display.fill((0, 0, 0))

        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
               100, 50, images['exit_sign'], lambda: False, None, bank_buttons)

        Button(50, 100, 50, 50, images['right_arrow'], None, 'first', bank_buttons)
        Button(50, 200, 50, 50, images['right_arrow'], None, 'second', bank_buttons)
        Button(50, 300, 50, 50, images['right_arrow'], None, 'third', bank_buttons)

        Button(100 + main_display.get_width(), 100, 50, 50, images['left_arrow'], None, 'fourth', bank_buttons)
        Button(100 + main_display.get_width(), 200, 50, 50, images['left_arrow'], None, 'fifth', bank_buttons)
        Button(100 + main_display.get_width(), 300, 50, 50, images['left_arrow'], None, 'sixth', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('1', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4, 470, 50, 50, image, None, '1', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('2', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 470, 50, 50, image, None, '2', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('3', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 2, 470, 50, 50, image, None, '3', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('4', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4, 545, 50, 50, image, None, '4', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('5', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 545, 50, 50, image, None, '5', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('6', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 2, 545, 50, 50, image, None, '6', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('7', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4, 620, 50, 50, image, None, '7', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('8', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 620, 50, 50, image, None, '8', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('9', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 2, 620, 50, 50, image, None, '9', bank_buttons)

        image = load_image('data/objects/digit_button.png')
        image.blit(render_text('0', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75, 670, 50, 50, image, None, '0', bank_buttons)

        image = load_image('data/objects/long_button.png')
        image.blit(render_text('Enter', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 3, 620, 208, 47, image, None, 'enter', bank_buttons)

        image = load_image('data/objects/long_button.png')
        image.blit(render_text('Clear', color=(0, 0, 0)), (10, 5))
        Button(100 + main_display.get_width() // 4 + 75 * 3, 545, 208, 47, image, None, 'clear', bank_buttons)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in bank_buttons:
                        if btn.rect.collidepoint(event.pos):
                            if not btn.id:
                                running = btn.run()
                            elif mode == 'error':
                                mode = 'main'
                                current_year = ''
                                math = ''
                                answer = ''
                            elif mode == 'main' and btn.id.isdigit():
                                current_year += btn.id
                            elif btn.id == 'enter' and mode == 'main':
                                if len(current_year) != 4:
                                    mode = 'error'
                                else:
                                    mode = 'math'
                                    a = randint(100, 999)
                                    b = randint(100, 999)
                                    right_answer = str(a + b)
                                    math = f'{a} + {b}'
                            elif mode == 'math' and btn.id.isdigit():
                                answer += btn.id
                            elif mode == 'math' and btn.id == 'enter':
                                if right_answer == answer:
                                    if random() < 0.75:
                                        player.infected = 3
                                        mode = 'infected'
                                    else:
                                        mode = 'ok'
                                        player.infected = 2
                                else:
                                    mode = 'error'

                            pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, button_group)
            data = pygame.key.get_pressed()
            player.set_moving(False)
            if data[27]:
                menu(pause=True)
                button_group.empty()
                pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

            main_display.fill((0, 0, 0))
            if mode == 'main':
                main_display.blit(
                    render_text('Введите ваш год рождения,', color=(232, 208, 79)),
                    (main_display.get_width() // 8, main_display.get_height() // 2 - 50))
                main_display.blit(
                    render_text('если вы хотите сдать анализы', color=(232, 208, 79)),
                    (main_display.get_width() // 8, main_display.get_height() // 2))

                main_display.blit(render_text(('_' * (4 - len(current_year))).rjust(4, '*'), color=(232, 208, 79)),
                                  (main_display.get_width() // 2, main_display.get_height() // 2 + 50))
            elif mode == 'math':
                main_display.blit(render_text('Решите простой пример, ', color=(232, 208, 79)),
                                  (main_display.get_width() // 8, main_display.get_height() // 2 - 50))
                main_display.blit(render_text('пока Ваши анализы готовятся...', color=(232, 208, 79)),
                                  (main_display.get_width() // 8, main_display.get_height() // 2))

                main_display.blit(render_text(math, color=(232, 208, 79)),
                                  (main_display.get_width() // 8, main_display.get_height() // 2 + 50))

                main_display.blit(render_text(('_' * (4 - len(current_year))).rjust(4, '*'), color=(232, 208, 79)),
                                  (main_display.get_width() // 2, main_display.get_height() // 2 + 100))
            elif mode == 'error':
                main_display.blit(
                    render_text('Ошибка! Попробуйте снова;)', color=(232, 208, 79)),
                    (main_display.get_width() // 4, main_display.get_height() // 2 - 50))
            elif mode == 'infected':
                main_display.blit(render_text('Вы инфецированы и заразны!', color=(232, 208, 79), size=35),
                                  (10, main_display.get_height() // 2 - 50))
                main_display.blit(render_text('Срочно необходима строгая изоляция!', color=(232, 208, 79), size=35),
                                  (10, main_display.get_height() // 2))
            elif mode == 'ok':
                main_display.blit(render_text('Вы здоровы!', color=(232, 208, 79)),
                                  (main_display.get_width() // 4, main_display.get_height() // 2 - 50))
                main_display.blit(render_text('Но мы советуем оставаться дома!', color=(232, 208, 79)),
                                  (main_display.get_width() // 8, main_display.get_height() // 2))

            screen.fill((156, 65, 10))
            player.update_params()
            button_group.draw(screen)
            bank_buttons.draw(screen)
            screen.blit(player.render_info(background=(156, 65, 10)), (0, 0))
            screen.blit(main_display, (100, 70))
            pygame.display.flip()
            clock.tick(fps)
        bank_buttons.empty()
        button_group.empty()


class Product(pygame.sprite.Sprite):
    def __init__(self, x, y, name, image, price, describtion, *groups):
        super().__init__(groups)

        self.image = image
        self.small_image = pygame.transform.scale(self.image.copy(), (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)

        self.name = name
        self.price = price
        self.id = id
        self.description = describtion
        self.bought = False
        self.is_used = False
        self.pin = None

    def was_used(self):
        return self.is_used

    def can_be_bought(self):
        return not self.bought

    def buy(self):
        self.bought = True

    def set_pos(self, pos):
        self.rect.x, self.rect.y = pos

    def get_price(self):
        return self.price

    def get_info(self):
        return f'{self.name} за {self.price} рублей'

    def get_describtion(self):
        return self.description

    def get_id(self):
        return self.id

    def add_to_groups(self, *groups):
        for i in groups:
            i.add(self)

    def remove_from_groups(self, *groups):
        for i in groups:
            i.remove(self)

    def reset_groups(self):
        for i in self.groups():
            i.remove(self)

    def get_small_image(self):
        return self.small_image

    def render_info(self, background=(0, 0, 0), color=(255, 255, 255)):
        display = pygame.Surface((width // 2, height // 2 * 3))
        display.fill(background)
        # main image
        display.blit(self.image, (display.get_width() // 2 - self.image.get_width() // 2, 50))
        # main information about title and price
        display.blit(render_text(self.get_info(), color=color), (50, self.image.get_height() + 50 + 20))
        # info about effects
        pxl_num = 1
        for i in self.description:
            display.blit(render_text(i, color=color), (50, self.image.get_height() + 50 + 35 * pxl_num + 50))
            pxl_num += 1
        return display

    def use(self):
        if self.name == 'Маска':
            player.infection_rate += 300
        elif self.name == 'Спирт':
            player.infection_rate += 250
        elif self.name == 'Мыло':
            player.infection_rate += 200
        elif self.name == 'Витамины':
            player.infection_rate += 100
        else:
            player.infection_rate += 50
            player.health += 10
            if player.health > 100:
                player.health = 100
        self.is_used = True
        return True


class Equipment:
    table_width = 4
    table_height = 4

    def __init__(self, player):
        self.products = player.get_objects()

    def enter(self):
        def reset():
            product_buttons.empty()
            for i in range(Equipment.table_height):
                for j in range(Equipment.table_width):
                    index = i * Equipment.table_width + j
                    if index >= len(self.products):
                        break
                    if not self.products[index].was_used():
                        Button(50 + 50 * j, 50 + 50 * i, 50, 50, self.products[index].get_small_image(),
                               self.products[index].render_info, index, product_buttons)

        running = True

        Button(width - images['exit_sign'].get_width(), height - images['exit_sign'].get_height(),
               100, 50, images['exit_sign'], lambda: False, 'exit', product_buttons)
        reset()
        info_display = None
        use_btn = None
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in product_buttons:
                        if btn.rect.collidepoint(event.pos):
                            if btn.id == 'exit':
                                running = False
                            elif btn != use_btn:
                                info_display = btn.run()
                                if btn.id is not None:
                                    if use_btn:
                                        use_btn.kill()
                                    use_btn = Button(width - 300, height - 150, 300, 75, render_text('Использовать'),
                                                     self.products[int(btn.id)].use, None, product_buttons)
                            else:
                                btn.run()
                                reset()
                                if info_display:
                                    info_display.fill((156, 65, 10))
                if event.type == pygame.KEYUP:
                    if event.key == 9:  # TAB
                        running = False
            data = pygame.key.get_pressed()
            player.set_moving(False)
            if data[27]:
                menu(pause=True)
                button_group.empty()
                pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)
            screen.fill((156, 65, 10))
            player.update_params()
            if info_display:
                screen.blit(info_display, (width // 2, 50))
            button_group.draw(screen)
            product_buttons.draw(screen)
            screen.blit(player.render_info(background=(156, 65, 10)), (0, 0))
            pygame.display.flip()
            clock.tick(fps)
        product_buttons.empty()


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, image, func, id=None, *groups):
        groups = list(groups)
        super().__init__(groups)
        self.h = h
        self.w = w
        self.id = id
        self.image = image
        self.image.set_alpha(255)
        self.rect = self.image.get_rect()
        self.func = func
        self.rect.x, self.rect.y = x, y
        self.frames = [self.image] * 2
        self.frames[0].set_alpha(50)
        self.frames[1].set_alpha(300)
        self.image = self.frames[0]

    def run(self, *args):
        return self.func(*args)

    def check_selection(self, pos):
        if self.rect.collidepoint(pos):
            self.image = self.frames[1]
        else:
            self.image = self.frames[0]

    def is_obstacle(self):
        return False

    def update(self, *args):
        if args:
            pos = args[0]
            self.image.set_alpha(100)
            if self.rect.collidepoint(pos):
                self.image.set_alpha(255)


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        if player.rect.y < 0 or player.rect.y > height or player.rect.y - terrain.rect.y < 750:
            obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - height // 2 - 150)


def exit_game():
    global global_exit
    global_exit = True
    time.sleep(0.5)
    sys.exit()


def menu(pause=False):
    global menu_is_on
    if menu_is_on:
        return
    else:
        menu_is_on = True
    delt_width = 75

    def start():
        return 'start'

    def settings():
        def sound_effect_switch():
            global effects_on
            effects_on = not effects_on
            label = f"Эффекты {'вкл' if effects_on else 'выкл'}"

            canvas = pygame.Surface((315, 100))
            canvas.fill((181, 109, 2))
            text = render_text(label)
            canvas.blit(text, (canvas.get_width() // 2 - text.get_width() // 2,
                               canvas.get_height() // 2 - text.get_height() // 2))

            effects_button.image = canvas

        def music_switch():
            global music_on
            music_on = not music_on
            label = f"Музыка {'вкл' if music_on else 'выкл'}"
            canvas = pygame.Surface((315, 100))
            canvas.fill((181, 109, 2))
            text = render_text(label)
            canvas.blit(text, (canvas.get_width() // 2 - text.get_width() // 2,
                               canvas.get_height() // 2 - text.get_height() // 2))

            music_button.image = canvas
            if not music_on:
                for mu in music.values():
                    mu.stop()
            else:
                music['main'].play(-1)

        running = True
        pos = (0, 0)

        canvas = pygame.Surface((315, 100))
        canvas.fill((181, 109, 2))
        text = render_text(f"Музыка вкл")
        canvas.blit(text, (canvas.get_width() // 2 - text.get_width() // 2,
                           canvas.get_height() // 2 - text.get_height() // 2))

        music_button = Button(width // 2 - delt_width, height // 4, 315, 100, canvas,
                              music_switch, None, settings_buttons_group)

        canvas = pygame.Surface((315, 100))
        canvas.fill((181, 109, 2))
        text = render_text(f"Эффекты вкл")
        canvas.blit(text, (canvas.get_width() // 2 - text.get_width() // 2,
                           canvas.get_height() // 2 - text.get_height() // 2))

        effects_button = Button(width // 2 - delt_width, height // 4 * 2, 315, 100,
                                canvas, sound_effect_switch,
                                None, settings_buttons_group)

        canvas = pygame.Surface((315, 100))
        canvas.fill((181, 109, 2))
        text = render_text('Назад')
        canvas.blit(text, (
            canvas.get_width() // 2 - text.get_width() // 2, canvas.get_height() // 2 - text.get_height() // 2))

        Button(width // 2 - delt_width, height // 4 * 3, 315, 100, canvas, lambda: 'back', None, settings_buttons_group)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                elif event.type == pygame.MOUSEMOTION:
                    pos = event.pos
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    for btn in settings_buttons_group:
                        if btn.rect.collidepoint(pos):
                            running = btn.run() != 'back'
            screen.fill((219, 146, 72, 100))
            settings_buttons_group.update(pos)
            settings_buttons_group.draw(screen)
            pygame.display.flip()
            clock.tick(fps)

    running = True
    pos = (0, 0)
    label = 'Продолжить'
    canvas = pygame.Surface((200, 100))
    canvas.fill((181, 109, 2))
    text = render_text(label)
    canvas.blit(text,
                (
                    canvas.get_width() // 2 - text.get_width() // 2,
                    canvas.get_height() // 2 - text.get_height() // 2))
    Button(width // 2 - delt_width, height // 4, 200, 100, canvas, start, None, button_group)

    canvas = pygame.Surface((200, 100))
    canvas.fill((181, 109, 2))
    text = render_text('Настройки')
    canvas.blit(text,
                (canvas.get_width() // 2 - text.get_width() // 2, canvas.get_height() // 2 - text.get_height() // 2))
    Button(width // 2 - delt_width, height // 4 * 2, 200, 100, canvas, settings, None, button_group)

    canvas = pygame.Surface((200, 100))
    canvas.fill((181, 109, 2))
    text = render_text('Выход')
    canvas.blit(text,
                (canvas.get_width() // 2 - text.get_width() // 2, canvas.get_height() // 2 - text.get_height() // 2))
    Button(width // 2 - delt_width, height // 4 * 3, 200, 100, canvas, exit_game, 'exit', button_group)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            elif event.type == pygame.MOUSEMOTION:
                pos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                for btn in button_group:
                    if btn.rect.collidepoint(pos):
                        running = btn.run() != 'start'
        data = pygame.key.get_pressed()
        if data[9]:
            running = False
        screen.fill((219, 146, 72))
        button_group.update(pos)

        button_group.draw(screen)
        pygame.display.flip()
        clock.tick(fps)
    button_group.empty()
    settings_buttons_group.empty()
    menu_is_on = False
    return 1


with open('data/data_files/products.dat', mode='r', encoding='utf-8') as f:
    for i in f.readlines():
        data = i.split(r'\t')
        image = load_image(data[2], size=(50, 90))
        products[data[0]] = Product(0, 0, data[1], image, int(data[3]), data[4].split(r'\n'))

images = {'pause_button': load_image('data/other/pause_button.png', size=(50, 50)),
          'right_arrow': load_image('data/objects/arrow_button_right.png', size=(50, 50)),
          'left_arrow': load_image('data/objects/arrow_button_left.png', size=(50, 50)),
          'exit_sign': load_image('data/objects/exit_sign.png', size=(100, 50)),
          'room': load_image('data/inside/room.png', size=size),
          'radio': load_image('data/objects/radio.png')}
images['pause_button'].set_alpha(100)
fps = 30
running = True
clock = pygame.time.Clock()
info_clock = pygame.time.Clock()
pos = (0, 0)

# menu()
# internal_id = input('Enter internal id:   ')
internal_id = str(randint(1000, 9999))

backgr = pygame.sprite.Sprite(background_group)
backgr.image = load_image('data/textures/background.png', size=size)
backgr.rect = backgr.image.get_rect()

role = ['policeman', 'citizen']
#player = Player(3850, 1050, input('enter role:     '), player_group)
player = Player(3850, 1050, choice(role), player_group)
player.id = internal_id
terrain = Terrain(0, 0, all_sprites, terrain_group)
bank = Bank(350, 900, all_sprites, building_group)
home = MainHouse(3710, 700, building_group, all_sprites)
pharmacy = Pharmacy(5050, 675, building_group, all_sprites)
shop = Shop(5750, 650, building_group, all_sprites)
second_shop = SecondShop(7250, 720, building_group, all_sprites)
hospital = Hospital(2200, 800, building_group, all_sprites)

pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)

# print("client connected to server")
thread = threading.Thread(target=operate_player_data)
thread.start()
# thread.join(0.01)
connect_tick = 0

camera = Camera()
camera.update(player)

scanner_on = False
arrest_rate = 0

# home.enter()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in button_group:
                if btn.rect.collidepoint(event.pos):
                    btn.run()
                    button_group.empty()
                    pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)
        if event.type == pygame.KEYUP:
            if player.role == 'policeman' and event.key == 99:
                scanner_on = False
                print('scanner off')
            if event.key == 9:  # TAB
                eq = Equipment(player)
                eq.enter()
        if event.type == pygame.KEYDOWN:
            if player.role == 'policeman' and event.key == 99:
                print('scanner on')
                scanner_on = True

    data = pygame.key.get_pressed()

    # if any(data):
    # print(data.index(1))

    player.set_moving(False)
    if data[27]:
        menu(pause=True)
        button_group.empty()
        pause_button = Button(width - 50, 0, 50, 50, images['pause_button'], menu, None, button_group)
    if data[101]:
        if near_building:
            player.inside = True
            near_building.enter()
            player.inside = False
    if data[51]:
        if player.role == 'policeman':
            for i in remote_players:
                if pygame.sprite.collide_mask(i, player) and i.role == 'citizen':
                    if arrest_rate > 5000:
                        i.caught += 1
                        if i.caught >= 3:
                            caught_ids.append(i.id)
                        arrest_rate = 0

    if data[97]:
        player.move_left()
        player.set_moving(True)
    if data[100]:
        player.move_right()
        player.set_moving(True)
    if data[32]:
        player.jump()
    screen.fill((0, 0, 0))
    camera.update(player)
    for sprite in all_sprites:
        try:
            camera.apply(sprite)
        except AttributeError:
            sprite.kill()
    for sprite in remote_players:
        try:
            camera.apply(sprite)
        except AttributeError:
            sprite.kill()
    camera.apply(player)

    all_sprites.update()
    player_group.update()
    button_group.update(pos)

    remote_players.update(scanner_on)

    background_group.draw(screen)
    try:
        all_sprites.draw(screen)
    except AttributeError:
        pass
    terrain_group.draw(screen)
    button_group.draw(screen)
    screen.blit(player.render_info(), (0, 0))
    player_group.draw(screen)
    try:
        remote_players.draw(screen)
    except AttributeError:
        pass

    if near_building_message and near_building:
        screen.blit(render_text(near_building_message), (0, height - 50))
    pygame.display.flip()
    clock.tick(fps)
    connect_tick += 1
    arrest_rate += info_clock.tick()
    if global_exit:
        break
exit_game()
