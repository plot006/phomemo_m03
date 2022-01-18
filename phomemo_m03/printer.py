# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import PIL
from numpy import byte
import serial
import socket

from phomemo_m03 import _image_helper
import PIL.Image

FF = 0x0C
NAK = 0x15
CAN = 0x18
ESC = 0x1B
GS = 0x1D
US = 0x1F

""""
class BluSerial:
    def __init__(self, 指定MACアドレス, ポート番号):
        self.BTソケット = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        self.BTソケット.connect((指定MACアドレス, ポート番号))

    def プリンタへの書き出し(self, 出力バイト列):
        if type(出力バイト列) is list:
            出力バイト列 = bytes(出力バイト列)
        self.BTソケット.send(出力バイト列)

    def プリンタからの入力(self, 読み込みサイズ):
        return self.BTソケット.recv(読み込みサイズ)

    def フラッシュ(self):
        pass
"""


class Printer:
    # 経験的にわかった最大幅
    MAX_WIDTH = 576

    def __init__(self, ポート名="/dev/tty.M03", 指定MACアドレス=None):
        """
        self.入出力ポート: BluSerial | serial.Serial
        if 指定MACアドレス is not None:
            # チャンネルは、`sdptool browse`を実行して見つけることができますが、同じである必要があります。
            self.入出力ポート = BluSerial(指定MACアドレス, 6)

        else:
            self.入出力ポート = serial.Serial(ポート名, timeout=10)
        """
        self.入出力ポート = serial.Serial(ポート名, timeout=10)

    def プリンタへ出力(self, 出力するバイト列: bytes):
        self.入出力ポート.write(出力するバイト列)
        self.入出力ポート.flush()

    def プリンタからの入力(self, 入力バイト数):
        return self.入出力ポート.read(size=入力バイト数)

    # これらのコマンドは、AndroidアプリのPrinterUtils.javaと同じ順番になっています。
    def 設定_濃度(self, 値=2):
        self.プリンタへ出力(bytes([ESC, 0x4E, 0x04, 値]))

    def 設定_デバイスタイマー(self, val):
        self.プリンタへ出力(bytes([ESC, 0x4E, 0x07, val]))

    def 取得_シリアルナンバー(self):
        # PrinterUtilsではNAKを使っていますが、なぜかうまくいかないようです。
        # しかし、どうやらUSは動くようです。
        self.プリンタへ出力(bytes([US, 0x11, 0x13]))
        return int.from_bytes(
            self.プリンタからの入力(3)[2:],
            byteorder="little",
        )

    def 取得_ファームバージョン(self):
        self.プリンタへ出力(bytes([US, 0x11, 0x07]))
        受信応答 = self.プリンタからの入力(5)
        return f"{受信応答[4]}.{受信応答[3]}.{受信応答[2]}"

    def 取得_エネルギー(self):
        self.プリンタへ出力(bytes([US, 0x11, 0x08]))
        return int.from_bytes(self.プリンタからの入力(3)[2:], byteorder="little")

    def 取得_デバイスタイマー(self):
        self.プリンタへ出力(bytes([US, 0x11, 0x0E]))
        return int.from_bytes(self.プリンタからの入力(3)[2:], byteorder="little")

    def 取得_紙状態(self):
        self.プリンタへ出力(bytes([US, 0x11, 0x11]))
        return int.from_bytes(
            self.プリンタからの入力(3)[2:],
            byteorder="little",
        )

    def 初期化(self):
        self.プリンタへ出力(bytes([ESC, 0x40]))

    def print_line_feed(self):
        self.プリンタへ出力(bytes([0x0A]))

    def emphasized_on(self):
        self.プリンタへ出力(bytes([ESC, 0x45, 1]))

    def emphasized_off(self):
        self.プリンタへ出力(bytes([ESC, 0x45, 0]))

    def 左詰め(self):
        self.プリンタへ出力(bytes([ESC, 0x61, 0]))

    def 中央揃え(self):
        self.プリンタへ出力(bytes([ESC, 0x61, 1]))

    def 右詰め(self):
        self.プリンタへ出力(bytes([ESC, 0x61, 2]))

    def 紙カット(self):
        self.プリンタへ出力(bytes([GS, 0x56, 1]))

    def 紙部分カット(self):
        self.プリンタへ出力(bytes([GS, 0x56, 0x42, 0]))

    # 注：設定_濃度()とプリント_濃度()の違いがよくわかりませんが、
    # こちらは非標準のコマンドを使用しているようです。
    def プリント_濃度(self, val):
        self.プリンタへ出力(bytes([NAK, 0x11, 0x02, val]))

    # これらのコマンドは、すでに上で述べたものを除いて、
    # PrintCommands.javaと同じ順序である。
    def print_feed_lines(self, num):
        self.プリンタへ出力(bytes([ESC, 0x64, num]))

    def print_feed_paper(self, num):
        self.プリンタへ出力(bytes([ESC, 0x4A, num]))

    def リセット(self):
        self.プリンタへ出力(bytes([ESC, 0x40, 0x02]))

    def バイトアレイ画像の印刷(self, バイト列リスト: list[bytearray]):
        """最下位のプリントイメージコマンドです。

        linesには、印刷する行を表すバイトアレイのリストを指定します。
        行の長さは8の倍数で、行数は256以下でなければなりません。
        pixel には0または1を指定してください。

        M03の場合、フルワイド画像は幅512ピクセルです。
        """
        モード = 0
        # CS v 0
        出力バイト列: bytearray = bytearray([GS, 0x76, 0x30, モード])

        幅: int = len(バイト列リスト[0])
        高さ: int = len(バイト列リスト)

        if 幅 % 8 != 0:
            raise ValueError("幅が8の倍数ではない")

        バイト幅: int = 幅 // 8

        出力バイト列.extend(バイト幅.to_bytes(2, byteorder="little"))

        if 高さ > 255:
            raise ValueError("高さが256未満ではない")

        出力バイト列.extend(高さ.to_bytes(2, byteorder="little"))

        for 高さ連番 in range(高さ):
            for 幅連番 in range(バイト幅):
                バイト: int = 0
                for ビット連番 in range(8):
                    ピクセル = バイト列リスト[高さ連番][幅連番 * 8 + ビット連番]
                    バイト |= (ピクセル & 0x01) << (7 - ビット連番)

                出力バイト列.append(バイト)

        self.プリンタへ出力(出力バイト列)

    # These are custom. :3
    def イメージ印刷(self, ファイル名, 印刷可能な最大幅=576, 上部空白に指定する高さ=5):
        with PIL.Image.open(ファイル名) as RGB画像:
            RGB画像 = _image_helper.画像のRGB変換(RGB画像, 印刷可能な最大幅)

        for 分割された画像 in _image_helper.チャンクに分割して都度返す(RGB画像, 上部空白に指定する高さ):
            self.バイトアレイ画像の印刷(_image_helper.画像のバイトアレイ変換(分割された画像))

        self.紙カット()
