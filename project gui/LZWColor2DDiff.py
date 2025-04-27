#!/usr/bin/env python3
import os
import math
import struct
import numpy as np
from PIL import Image

class LZWColor2DDiffCoding:
    def __init__(self, filename, data_type):
        """
        Level 5: 2D fark (satır ve sütun farkı) tabanlı LZW sıkıştırma/açma.
        Bu sürümde farklar, (current - neighbor) mod 256 şeklinde hesaplanır.
        filename: dosya adının uzantısız kısmı (örneğin, 'lena_color')
        data_type: 'image'
        """
        self.filename = filename
        self.data_type = data_type
        self.code_length_R = None
        self.code_length_G = None
        self.code_length_B = None

    def compress_image_file(self):
        """
        1) Renkli görüntüyü (RGB) oku.
        2) Her kanalda 2D fark matrisini hesapla (mod 256):
           - (0,0): ham piksel değeri,
           - (0,c>0): (pixel[0,c] - pixel[0,c-1]) mod 256,
           - (r>0, c=0): (pixel[r,0] - pixel[r-1,0]) mod 256,
           - (r>0, c>0): (pixel[r,c] - pixel[r,c-1]) mod 256.
        3) Her fark matrisini 1D listeye çevirip LZW sıkıştırması uygula.
        4) Her kanalın bit string’ini oluştur, padding ekle, byte array’e çevir.
        5) Meta bilgileri (width, height, her kanal için code_length, padding miktarı, veri uzunluğu) ile
           tüm veriyi .bin dosyasına yaz.
        """
        current_dir = os.path.dirname(os.path.realpath(__file__))
        input_path = os.path.join(current_dir, self.filename + '.png')
        output_path = os.path.join(current_dir, self.filename + '.bin')

        # 1) Görüntüyü oku ve RGB’ye çevir
        img = Image.open(input_path).convert('RGB')
        pixel_array = np.array(img, dtype=np.uint8)
        height, width, _ = pixel_array.shape

        # 2) R, G, B kanallarını ayır ve 2D fark matrislerini oluştur
        R = pixel_array[..., 0]
        G = pixel_array[..., 1]
        B = pixel_array[..., 2]

        diff_R = self.create_2d_difference(R)
        diff_G = self.create_2d_difference(G)
        diff_B = self.create_2d_difference(B)

        # 3) Fark matrislerini flatten edip LZW ile sıkıştır
        diff_R_list = diff_R.flatten().tolist()
        diff_G_list = diff_G.flatten().tolist()
        diff_B_list = diff_B.flatten().tolist()

        encoded_R, dict_size_R = self.encode_channel(diff_R_list)
        encoded_G, dict_size_G = self.encode_channel(diff_G_list)
        encoded_B, dict_size_B = self.encode_channel(diff_B_list)

        self.code_length_R = max(1, math.ceil(math.log2(dict_size_R)))
        self.code_length_G = max(1, math.ceil(math.log2(dict_size_G)))
        self.code_length_B = max(1, math.ceil(math.log2(dict_size_B)))

        # 4) Bit string’e çevir, padding ekle, byte array oluştur
        bit_R = self.int_list_to_bitstring(encoded_R, self.code_length_R)
        padded_R, extra_pad_R = self.pad_bitstring(bit_R)
        byte_array_R = self.bitstring_to_byte_array(padded_R)

        bit_G = self.int_list_to_bitstring(encoded_G, self.code_length_G)
        padded_G, extra_pad_G = self.pad_bitstring(bit_G)
        byte_array_G = self.bitstring_to_byte_array(padded_G)

        bit_B = self.int_list_to_bitstring(encoded_B, self.code_length_B)
        padded_B, extra_pad_B = self.pad_bitstring(bit_B)
        byte_array_B = self.bitstring_to_byte_array(padded_B)

        # 5) Dosyaya meta bilgileri ve verileri yaz
        with open(output_path, 'wb') as f:
            # Görüntü boyutları: width (4B) ve height (4B)
            f.write(struct.pack('>I', width))
            f.write(struct.pack('>I', height))
            # R kanalı: code_length (2B), padding (1B), veri uzunluğu (4B), veri
            f.write(struct.pack('>H', self.code_length_R))
            f.write(struct.pack('>B', extra_pad_R))
            f.write(struct.pack('>I', len(byte_array_R)))
            f.write(byte_array_R)
            # G kanalı:
            f.write(struct.pack('>H', self.code_length_G))
            f.write(struct.pack('>B', extra_pad_G))
            f.write(struct.pack('>I', len(byte_array_G)))
            f.write(byte_array_G)
            # B kanalı:
            f.write(struct.pack('>H', self.code_length_B))
            f.write(struct.pack('>B', extra_pad_B))
            f.write(struct.pack('>I', len(byte_array_B)))
            f.write(byte_array_B)

        original_size = width * height * 3
        compressed_size = os.path.getsize(output_path)
        print(f"{self.filename}.png is compressed into {self.filename}.bin.")
        print(f"Original pixel count: {original_size} bytes")
        print(f"Compressed file size: {compressed_size} bytes")
        if original_size:
            print(f"Compression Ratio: {compressed_size/original_size:.3f}")

    def create_2d_difference(self, channel_array):
        """
        Her kanalda 2D fark hesaplar (mod 256):
          - (0,0): diff = pixel[0,0]
          - (0, c>0): diff = (pixel[0,c] - pixel[0,c-1]) mod 256
          - (r>0, 0): diff = (pixel[r,0] - pixel[r-1,0]) mod 256
          - (r>0, c>0): diff = (pixel[r,c] - pixel[r,c-1]) mod 256
        """
        h, w = channel_array.shape
        diff_array = np.zeros((h, w), dtype=np.uint8)
        for r in range(h):
            for c in range(w):
                val = int(channel_array[r, c])
                if r == 0 and c == 0:
                    diff_array[r, c] = val
                elif r == 0:
                    left = int(channel_array[r, c-1])
                    diff_array[r, c] = (val - left) % 256
                elif c == 0:
                    up = int(channel_array[r-1, c])
                    diff_array[r, c] = (val - up) % 256
                else:
                    left = int(channel_array[r, c-1])
                    diff_array[r, c] = (val - left) % 256
        return diff_array

    def encode_channel(self, data_list):
        """
        Klasik LZW sıkıştırması (verilen data_list üzerinde).
        data_list: 0..255 aralığındaki fark değerleri.
        """
        dict_size = 256
        dictionary = { (i,): i for i in range(dict_size) }
        w = []
        encoded = []
        for val in data_list:
            w_plus = w + [val]
            if tuple(w_plus) in dictionary:
                w = w_plus
            else:
                encoded.append(dictionary[tuple(w)])
                dictionary[tuple(w_plus)] = dict_size
                dict_size += 1
                w = [val]
        if w:
            encoded.append(dictionary[tuple(w)])
        return encoded, dict_size

    def int_list_to_bitstring(self, codes, code_length):
        return "".join(format(c, f'0{code_length}b') for c in codes)

    def pad_bitstring(self, bitstring):
        extra_padding = (8 - len(bitstring) % 8) % 8
        padded = bitstring + ('0' * extra_padding)
        return padded, extra_padding

    def bitstring_to_byte_array(self, bitstring):
        if len(bitstring) % 8 != 0:
            raise ValueError("Bitstring length not multiple of 8.")
        return bytearray(int(bitstring[i:i+8], 2) for i in range(0, len(bitstring), 8))

    def decompress_image_file(self):
        """
        1) .bin dosyasını oku; width, height, her kanal için meta bilgileri al.
        2) Her kanalın bit verisini LZW decode ile fark listesine çevir.
        3) Fark listesini 2D matris haline getir ve ters fark işlemiyle orijinal piksel değerlerini hesapla.
        4) R, G, B kanallarını birleştirip .png olarak kaydet.
        """
        current_dir = os.path.dirname(os.path.realpath(__file__))
        input_path = os.path.join(current_dir, self.filename + '.bin')
        output_path = os.path.join(current_dir, self.filename + '_decompressed.png')

        with open(input_path, 'rb') as f:
            width = struct.unpack('>I', f.read(4))[0]
            height = struct.unpack('>I', f.read(4))[0]

            self.code_length_R = struct.unpack('>H', f.read(2))[0]
            extra_pad_R = struct.unpack('>B', f.read(1))[0]
            len_R = struct.unpack('>I', f.read(4))[0]
            data_R = f.read(len_R)

            self.code_length_G = struct.unpack('>H', f.read(2))[0]
            extra_pad_G = struct.unpack('>B', f.read(1))[0]
            len_G = struct.unpack('>I', f.read(4))[0]
            data_G = f.read(len_G)

            self.code_length_B = struct.unpack('>H', f.read(2))[0]
            extra_pad_B = struct.unpack('>B', f.read(1))[0]
            len_B = struct.unpack('>I', f.read(4))[0]
            data_B = f.read(len_B)

        diff_R = self.decompress_channel(data_R, self.code_length_R, extra_pad_R, height, width)
        diff_G = self.decompress_channel(data_G, self.code_length_G, extra_pad_G, height, width)
        diff_B = self.decompress_channel(data_B, self.code_length_B, extra_pad_B, height, width)

        R_arr = self.reconstruct_2d_diff(diff_R)
        G_arr = self.reconstruct_2d_diff(diff_G)
        B_arr = self.reconstruct_2d_diff(diff_B)

        R_arr = np.clip(R_arr, 0, 255).astype(np.uint8)
        G_arr = np.clip(G_arr, 0, 255).astype(np.uint8)
        B_arr = np.clip(B_arr, 0, 255).astype(np.uint8)

        color_array = np.dstack((R_arr, G_arr, B_arr))
        Image.fromarray(color_array, 'RGB').save(output_path)
        print(f"{self.filename}.bin is decompressed into {self.filename}_decompressed.png.")

    def decompress_channel(self, byte_data, code_length, extra_pad, height, width):
        bitstring = "".join(format(b, '08b') for b in byte_data)
        if extra_pad > 0:
            bitstring = bitstring[:-extra_pad]
        codes = []
        for i in range(0, len(bitstring), code_length):
            chunk = bitstring[i:i+code_length]
            if len(chunk) < code_length:
                break
            codes.append(int(chunk, 2))
        diff_list = self.decode_channel(codes)
        if len(diff_list) != width * height:
            raise ValueError("Decoded data size mismatch for channel.")
        diff_array = np.array(diff_list, dtype=np.uint8).reshape((height, width))
        return diff_array

    def decode_channel(self, codes):
        dict_size = 256
        dictionary = { i: [i] for i in range(dict_size) }
        w = dictionary[codes[0]][:]
        result = w[:]
        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code][:]
            elif code == dict_size:
                entry = w + [w[0]]
            else:
                raise ValueError(f"Bad compressed code: {code}")
            result.extend(entry)
            dictionary[dict_size] = w + [entry[0]]
            dict_size += 1
            w = entry
        return result

    def reconstruct_2d_diff(self, diff_array):
        """
        Reconstruct the original channel from its 2D difference matrix.
        For each channel, we assume:
          - (0,0): pixel[0,0] = diff[0,0]
          - (0,c>0): pixel[0,c] = (pixel[0,c-1] + diff[0,c]) mod 256
          - (r>0,0): pixel[r,0] = (pixel[r-1,0] + diff[r,0]) mod 256
          - (r>0,c>0): pixel[r,c] = (pixel[r,c-1] + diff[r,c]) mod 256
        """
        h, w = diff_array.shape
        pixel_array = np.zeros((h, w), dtype=np.int16)
        for r in range(h):
            for c in range(w):
                if r == 0 and c == 0:
                    pixel_array[r, c] = diff_array[r, c]
                elif r == 0:
                    pixel_array[r, c] = (pixel_array[r, c-1] + diff_array[r, c]) % 256
                elif c == 0:
                    pixel_array[r, c] = (pixel_array[r-1, c] + diff_array[r, c]) % 256
                else:
                    pixel_array[r, c] = (pixel_array[r, c-1] + diff_array[r, c]) % 256
        return pixel_array
