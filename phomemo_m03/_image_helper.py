# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import math

import PIL
import PIL.Image
import PIL.ImageOps


def 画像のRGB変換(画像: PIL.Image.Image, 印刷可能な最大幅: int = 576, ファイル保存する場合: bool = False) -> PIL.Image.Image:
    画像の幅, 画像の高さ = 画像.size
    アスペ比 = 画像の幅 / 画像の高さ
    調整後サイズ = (印刷可能な最大幅, math.floor(印刷可能な最大幅 / アスペ比))
    リサイズした画像: PIL.Image.Image = 画像.resize(調整後サイズ)
    リサイズした画像.save("_resize.png")
    反転した画像: PIL.Image.Image = PIL.ImageOps.invert(リサイズした画像.convert("RGB"))
    反転した画像.save("_invert.png")
    コンバートした画像: PIL.Image.Image = 反転した画像.convert("1")

    if ファイル保存する場合:
        コンバートした画像.save("converted.png")

    return コンバートした画像


def チャンクに分割して都度返す(分割する画像: PIL.Image.Image, 上部空白に指定する高さ: int):
    分割数 = 分割する画像.height // 255

    # プリンタが最初の数行を印刷しない場合の回避策として、1つの「空の」チャンクを出力します。
    yield 空白イメージを生成して返す(空白の幅=分割する画像.width, 空白の高さ=上部空白に指定する高さ)

    for 分割番号 in range(分割数 + 1):
        左端 = 0
        上端 = 分割番号 * 255
        右端 = 分割する画像.width
        下端 = 分割番号 * 255 + 255
        返す画像 = 切り出しイメージ_余白はcropでトリム済み = 分割する画像.crop((左端, 上端, 右端, 下端))
        yield 返す画像


def 画像のバイトアレイ変換(画像, しきい値=127):
    return [
        bytearray(
            [
                1 if 画像.getpixel((x, y)) > しきい値 else 0
                for x in range(画像.width)
            ]
        )
        for y in range(画像.height)
    ]


def 空白イメージを生成して返す(空白の幅, 空白の高さ):
    return PIL.Image.new("L", (空白の幅, 空白の高さ), color=0)
