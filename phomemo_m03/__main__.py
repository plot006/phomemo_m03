# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import argparse
import sys

import PIL.Image
import PIL.ImageDraw

import phomemo_m03.printer
import phomemo_m03._image_helper


def _テストイメージ生成(幅):
    生成イメージ = PIL.Image.new("RGB", (幅, 30), (255, 255, 255))
    ドロワー = PIL.ImageDraw.Draw(生成イメージ)
    ドロワー.rectangle((10, 10, 生成イメージ.width - 10, 生成イメージ.height - 10), fill=(0, 0, 0))
    ドロワー.rectangle((0, 0, 生成イメージ.width - 1, 生成イメージ.height - 1), outline=(0, 0, 0))

    生成イメージ.save("test.png")

    return "test.png"


if __name__ == "__main__":
    引数パーサ = argparse.ArgumentParser()
    引数パーサ.add_argument("image")
    引数パーサ.add_argument(
        "--width", type=int, default=phomemo_m03.printer.Printer.MAX_WIDTH
    )
    引数パーサ.add_argument("--test", action="store_true", default=False)
    引数パーサ.add_argument("--convert-only", action="store_true", default=False)
    引数パーサ.add_argument("--port", default="/dev/tty.M03")
    引数パーサ.add_argument("--mac", default=None)

    引数 = 引数パーサ.parse_args()

    if 引数.test:
        引数.image = _テストイメージ生成(引数.width)

    if 引数.convert_only:
        with PIL.Image.open(引数.image) as 読み込みイメージ:
            phomemo_m03._image_helper.画像のRGB変換(
                読み込みイメージ, 印刷可能な最大幅=引数.width, ファイル保存する場合=True
            )
        sys.exit(0)

    プリンタ = phomemo_m03.printer.Printer(引数.port, 引数.mac)
    プリンタ.初期化()
    プリンタ.リセット()
    print("Serial number:", プリンタ.取得_シリアルナンバー())
    print("Firmware:", プリンタ.取得_ファームバージョン())
    print("Paper state:", プリンタ.取得_紙状態())
    print("Energy:", プリンタ.取得_エネルギー())

    プリンタ.初期化()
    プリンタ.左詰め()

    プリンタ.イメージ印刷(引数.image, 印刷可能な最大幅=引数.width)

    プリンタ.リセット()
