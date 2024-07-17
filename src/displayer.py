


import numpy as np
import cv2

from .frame import NPFrame

# ASCII_CHARS = '@%#*+=-:. '
ASCII_CHARS = " .,-:;i1tfLCG08@"
from ascii_magic import AsciiArt
from PIL import Image, ImageEnhance

class Displayer:
    def render(self, frame:NPFrame) -> None:
        # self.rgb_to_ascii(frame)
        img = Image.fromarray(frame.data.transpose(2, 1, 0))
        my_art = AsciiArt.from_pillow_image(img, )
        my_art.to_terminal(columns=50,)
        pass


    # def rgb_to_ascii(self, image:np.ndarray):
    #     ascii_str = ''
    #     W = image.shape[2]
    #     H = image.shape[1]

    #     # 将 RGB 图像转换为 ASCII
    #     for row in range(H):
    #         for col in range(W):
    #             pixel = image[:, row, col]
    #             # 计算字符索引
    #             r, g, b = pixel[0], pixel[1], pixel[2]
    #             # 使用明度值来选择 ASCII 字符
    #             gray = (r*299 + b*587 + b*114 + 500) / 1000
    #             # gray = (r + g + b) // 3
    #             brightness = int(gray) // len(ASCII_CHARS) - 1
    #             ascii_str += ASCII_CHARS[brightness]
    #             ascii_str += "\033[38;2;{:d};{:d};{:d}m{:s}\033[0m".format(int(r), int(g), int(b), ASCII_CHARS[brightness])  # 带颜色的字符
    #         ascii_str += '\n'
        
    #     print(ascii_str)
    #     # return ascii_str


if __name__ == '__main__':
    img = cv2.imread("assert/1.png", cv2.COLOR_BGR2RGB)
    # img=cv2.resize(img, (20, 20))
    # img=img.transpose((2, 0, 1))
    d = Displayer()
    # frame = np.random.randint(0, 255, size=(3, 20, 20), dtype=np.uint8)
    d.render(img)
    # print("\033[38;2;255;0;0m这是红色\033[0m")
    # print("\033[38;2;0;255;0m这是绿色\033[0m")
    # print("\033[38;2;0;0;255m这是蓝色\033[0m")
    # print("\033[38;2;255;255;0m这是黄色\033[0m")
    # print("\033[38;2;0;255;255m这是青色\033[0m")
    # print("\033[38;2;255;0;255m这是洋红色\033[0m")
    # print("\033[38;2;255;255;255m这是白色\033[0m")