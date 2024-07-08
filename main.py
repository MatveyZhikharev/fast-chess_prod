import json  # работа с json
from PIL import Image  # генерация изображений
from stockfish import Stockfish  # работа с движком
from flask import Flask, request  # для принятия и отправки запросов
from YandexImages import YandexImages  # загрузка изображений

from REFERENCES import *

IMAGES = {"r": "images/BlackRook.png",
          "n": "images/BlackKnight.png",
          "b": "images/BlackBishop.png",
          "k": "images/BlackKing.png",
          "q": "images/BlackQueen.png",
          "p": "images/BlackPawn.png",
          "R": "images/WhiteRook.png",
          "N": "images/WhiteKnight.png",
          "B": "images/WhiteBishop.png",
          "K": "images/WhiteKing.png",
          "Q": "images/WhiteQueen.png",
          "P": "images/WhitePawn.png"}  # изображения фигур

RULES = (
    "Сейчас я научу тебя играть в шахматы.\nМы играем по очереди. "
    "Вы имеете право перемещать по одной фигуре за каждый ход.\n"
    "Если перемещаемая вами фигура заканчивает свой ход на поле, занятой моей фигурой, "
    "то вы можете взять или «съесть» мою фигуру.\n"
    "Как только вы сделаете ход, который приведёт к тупику моего короля, вы выиграете."
    "Нельзя делать ход, который подвергает вашего короля атаке. "
)

BOARD = [["r", "n", "b", "q", "k", "b", "n", "r"],
         ["p", "p", "p", "p", "p", "p", "p", "p"],
         ["", "", "", "", "", "", "", ""],
         ["", "", "", "", "", "", "", ""],
         ["", "", "", "", "", "", "", ""],
         ["", "", "", "", "", "", "", ""],
         ["P", "P", "P", "P", "P", "P", "P", "P"],
         ["R", "N", "B", "Q", "K", "B", "N", "R"]]  # начальное расположение фигур

AGREEMENTS = {"ага",
              "го", "гоу",
              "да", "давай", "давай",
              "конечно",
              "проблем",
              "разумеется", }

stockfish = Stockfish("stockfish_15.1_win_x64_avx2/stockfish_15.1_win_x64_avx2/stockfish-windows-2022-x86-64-avx2.exe")

yandex = YandexImages()
yandex.set_auth_token(token=TOKEN)
yandex.skills = SKILL

app = Flask(__name__)


def return_msg(text="", tts=None, buttons=[], card=None):  # возвращает json-подобное сообщение
    return {
        "response": {
            "text": text,  # основной текст
            "tts": tts if tts else text,  # произношение
            "buttons": buttons,
            "card": card,  # изображение
            "end_session": False,
            "directives": {}
        },
        "session_state": {
            "value": 10
        },
        "user_state_update": {
            "value": 42
        },
        "application_state": {
            "value": 37
        },
        "version": "1.0"
    }


def make_card(id, type="BigImage", title=None, description=None):  # возвращает правильно оформленную картинку
    return {
        "type": type,
        "image_id": id,
        "title": title,
        "description": description
    }


def return_step(step):  # Алиса коверкает ходы, эта функция их нормализует
    rus_to_eng = {"а": "a",
                  "б": "b",
                  "ц": "c",
                  "с": "c",
                  "д": "d",
                  "е": "e",
                  "ф": "f",
                  "г": "g",
                  "х": "h",
                  }
    step = list("".join("".join(step.split("-")).split()))
    if step[-1] == ".":
        step = step[:-1]

    print(step)
    if len(step) == 4:
        step[0] = rus_to_eng.get(step[0], step[0])
        step[2] = rus_to_eng.get(step[2], step[2])
        step = "".join(step)
        return step
    return False


@app.route('/', methods=['POST'])
def handler():  # главная функция
    def save():  # сохраняет данные о данные
        with open('data.json', 'w') as file:
            json.dump(data, file)

    with open('data.json') as json_file:
        data = json.load(json_file)
    input_json = request.get_json()
    msg = input_json["request"]["command"]
    user_id = input_json["session"]["user"]["user_id"]
    if "правила" in msg:
        return return_msg(RULES)
    user = data.get(user_id, {})
    if not user:
        user["last_command"] = "start"
        user["skill"] = 10
        user["board"] = BOARD
        user["steps"] = []
        data[user_id] = user
        save()
        return return_msg("Привет, сыграем партеечку в шахматы?")
    elif input_json["session"]["new"]:
        user["last_command"] = "start"
        save()
        buttons = []
        resp = "Сыграем?"
        if user["steps"]:
            [buttons.append(
                {
                    'title': ans.title(),
                    'hide': True
                }
            ) for ans in ("доиграть", "новая")]
            resp = (
                "У вас есть недоигранная партия напишите \"доиграть\", чтобы продолжить или начните новую, "
                "сказав \"новая\""
            )
        return return_msg(f"Рада тебя видеть снова! {resp}", buttons=buttons)
    if user["last_command"] == "start":
        if "доигр" in msg or "продолж" in msg:
            user["last_command"] = "game"
            save()
            stockfish.set_position(user["steps"])
            return return_msg(card=make_card(print_image(), title="Продолжаем игру"))
        if AGREEMENTS.intersection(set(input_json["request"]["nlu"]["tokens"])):
            user["last_command"] = "game"
            user["steps"] = []
            save()
            return return_msg(card=make_card(print_image(), title="Ваш ход"))
    if "нов" in msg:
        user["board"] = BOARD
        user["steps"] = []
        data[user_id] = user
        save()
        return return_msg("Начинаем новую игру")
    stockfish.set_position(user["steps"])
    stockfish.set_skill_level(user["skill"])
    if "уров" in msg:
        user["last_command"] = "lvl"
        data[user_id] = user
        save()
        return return_msg("Введите число от 1 до 25")
    if user["last_command"] == "lvl":
        if num := tuple(filter(lambda x: x.isdigit() and 1 <= int(x) <= 25, msg.split()))[-1]:
            user["skill"] = num
            data[user_id] = user
            user["last_command"] = "game"
            save()
            return return_msg(f"Уровень изменён на {user['skill']}")
        return return_msg("Введите число от 1 до 25")
    if "подсказ" in msg:
        return return_msg(stockfish.get_best_move())
    if step := return_step(msg):
        if stockfish.is_move_correct(step):
            steps = user["steps"]
            stockfish.make_moves_from_current_position([step])
            stockfish.make_moves_from_current_position([m := stockfish.get_best_move()])
            steps.extend([step, m])
            save()

            return return_msg(card=make_card(print_image(), title=m))
        print(stockfish.get_board_visual())
        return return_msg("Ход некоректен или его не возможно совершить")
    print(user)
    return return_msg("Я тебя не понял повтори пожалуйста")


def make_step(step):
    if stockfish.is_move_correct(step):
        stockfish.make_moves_from_current_position([step, stockfish.get_best_move()])


def make_board():  # возвращает список фигур в формате, как в строке 27
    return [[x for x in line[2:31].split(" | ")]
            for line in stockfish.get_board_visual().split("\n")[1:16:2]]


def print_image():  # сохраняет доску с фигурами
    board = make_board()
    im = Image.open("images/desk2.png")
    for row in range(8):
        for col in range(8):
            im2 = IMAGES.get(board[row][col], None)
            if im2:
                im2 = Image.open(im2)
                im.paste(im2, (355 + col * 55, row * 54 - 10), mask=im2)
    im.save("images/res.png")
    return yandex.downloadImageFile("images/res.png")["id"]


if __name__ == '__main__':
    app.run()