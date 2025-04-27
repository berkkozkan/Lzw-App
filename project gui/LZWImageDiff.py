#!/usr/bin/env python3
import os
import math
import struct
import numpy as np
from PIL import Image

class LZWImageDiffCoding:
    def __init__(self, filename, data_type):
        self.filename = filename      # Örn: 'lena_diff'
        self.data_type = data_type    # 'image'
        self.codelength = None
        self.offset = 128            # Farkları 0..255 aralığına çekmek için

    def compress_image_file(self):
        """
        1) .png dosyasını gri seviye olarak oku
        2) Piksel farklarını (difference image) hesapla
        3) LZW sıkıştırma
        4) Sonucu .bin dosyasına yaz (meta bilgiler + sıkıştırılmış veriler)
        """
        current_directory = os.path.dirname(os.path.realpath(__file__))
        input_file = self.filename + '.png'
        input_path = os.path.join(current_directory, input_file)
        output_file = self.filename + '.bin'
        output_path = os.path.join(current_directory, output_file)

        # 1) Görüntüyü gri seviye oku
        img = Image.open(input_path).convert('L')
        pixel_array = np.array(img)
        height, width = pixel_array.shape

        # 2) Fark matrisi oluştur (satır içi fark)
        diff_array = self.create_difference_image(pixel_array)

        # 2D -> 1D liste
        diff_list = diff_array.flatten().tolist()

        # 3) LZW sıkıştırma (difference listesi)
        encoded_codes = self.encode(diff_list)

        # Kodlar bit string'e dönüştürülüp padding eklenir
        bitstring = self.int_list_to_binary_string(encoded_codes)
        padded_bitstring = self.pad_encoded_data(bitstring)
        byte_array = self.get_byte_array(padded_bitstring)

        # 4) Meta bilgileri (width, height, codelength, offset) + veriyi dosyaya yaz
        with open(output_path, 'wb') as f:
            # width, height, codelength, offset
            f.write(struct.pack('>I', width))    # 4 byte
            f.write(struct.pack('>I', height))   # 4 byte
            f.write(struct.pack('>H', self.codelength))  # 2 byte
            f.write(struct.pack('>H', self.offset))      # 2 byte (offset)
            f.write(byte_array)

        print(f"{input_file} is compressed into {output_file}.")
        original_size = width * height  # ham piksel boyutu (byte)
        compressed_size = os.path.getsize(output_path)
        print(f"Original pixel count: {original_size} bytes")
        print(f"Compressed file size: {compressed_size} bytes")
        if original_size != 0:
            print(f"Compression Ratio: {compressed_size/original_size:.3f}")
        return output_path

    def create_difference_image(self, pixel_array):
        """
        Basit fark yaklaşımı: 
        - Her satırın ilk pikselini ham sakla
        - Diğer pikselleri: diff = current - left + offset
        """
        height, width = pixel_array.shape
        diff_array = np.zeros((height, width), dtype=np.uint8)

        for r in range(height):
            for c in range(width):
                if c == 0:
                    # İlk pikseli aynen sakla (fark yok)
                    diff_array[r, c] = pixel_array[r, c]
                else:
                    # fark = current - left + offset
                    val = (pixel_array[r, c] - pixel_array[r, c-1]) + self.offset
                    # 0..255 aralığına sığdığını varsayıyoruz
                    diff_array[r, c] = val
        return diff_array

    def encode(self, diff_list):
        """
        LZW sıkıştırma (piksel fark dizisi üzerinde).
        """
        dict_size = 256
        dictionary = { (i,): i for i in range(dict_size) }
        w = []
        result = []

        for val in diff_list:
            w_plus = w + [val]
            key = tuple(w_plus)
            if key in dictionary:
                w = w_plus
            else:
                result.append(dictionary[tuple(w)])
                dictionary[key] = dict_size
                dict_size += 1
                w = [val]
        if w:
            result.append(dictionary[tuple(w)])

        # Sözlük büyüklüğüne göre code length hesapla
        self.codelength = math.ceil(math.log2(dict_size))
        return result

    def int_list_to_binary_string(self, int_list):
        bitstring = ""
        for num in int_list:
            bitstring += format(num, '0{}b'.format(self.codelength))
        return bitstring

    def pad_encoded_data(self, bitstring):
        extra_padding = 8 - (len(bitstring) % 8)
        if extra_padding == 8:
            extra_padding = 0
        # ilk 8 bit'e extra_padding bilgisini koy
        header = format(extra_padding, '08b')
        padded = header + bitstring + ("0" * extra_padding)
        return padded

    def get_byte_array(self, padded_bitstring):
        if len(padded_bitstring) % 8 != 0:
            raise ValueError("Bit string length is not a multiple of 8.")
        b_array = bytearray()
        for i in range(0, len(padded_bitstring), 8):
            chunk = padded_bitstring[i:i+8]
            b_array.append(int(chunk, 2))
        return b_array

    def decompress_image_file(self):
        """
        1) .bin dosyasını oku (width, height, code_length, offset + sıkıştırılmış veri)
        2) LZW dekompresyon -> fark dizisi
        3) Fark dizisinden orijinal piksel değerlerini hesapla
        4) Kaydet (.png)
        """
        current_directory = os.path.dirname(os.path.realpath(__file__))
        input_file = self.filename + '.bin'
        input_path = os.path.join(current_directory, input_file)
        output_file = self.filename + '_decompressed.png'
        output_path = os.path.join(current_directory, output_file)

        with open(input_path, 'rb') as f:
            width = struct.unpack('>I', f.read(4))[0]
            height = struct.unpack('>I', f.read(4))[0]
            self.codelength = struct.unpack('>H', f.read(2))[0]
            self.offset = struct.unpack('>H', f.read(2))[0]
            compressed_bytes = f.read()

        # Byte array -> bit string
        bitstring = ""
        for byte in compressed_bytes:
            bitstring += format(byte, '08b')

        # ilk 8 bit = extra_padding
        extra_padding = int(bitstring[:8], 2)
        bitstring = bitstring[8:]
        if extra_padding > 0:
            bitstring = bitstring[:-extra_padding]

        # bit string -> integer kodlar
        codes = []
        for i in range(0, len(bitstring), self.codelength):
            chunk = bitstring[i:i+self.codelength]
            if len(chunk) < self.codelength:
                break
            val = int(chunk, 2)
            codes.append(val)

        # LZW dekompresyon -> fark listesi
        diff_list = self.decode(codes)

        # Fark listesi -> fark matrisi
        diff_array = np.array(diff_list, dtype=np.uint8).reshape((height, width))

        # Fark matrisinden orijinal piksel değerlerini geri al
        pixel_array = self.reconstruct_original(diff_array)

        # Kaydet
        img = Image.fromarray(pixel_array, 'L')
        img.save(output_path)

        print(f"{input_file} is decompressed into {output_file}.")
        return output_path

    def decode(self, codes):
        dict_size = 256
        dictionary = {i: [i] for i in range(dict_size)}
        w = dictionary[codes[0]]
        result = w[:]
        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code]
            elif code == dict_size:
                entry = w + [w[0]]
            else:
                raise ValueError(f"Bad compressed code: {code}")
            result.extend(entry)
            dictionary[dict_size] = w + [entry[0]]
            dict_size += 1
            w = entry
        return result

    def reconstruct_original(self, diff_array):
        """
        diff_array[r, 0] = orijinal piksel (ilk piksel)
        diff_array[r, c] = (pixel[r, c] - pixel[r, c-1]) + offset

        Orijinali geri almak için:
        pixel[r, c] = diff_array[r, c] - offset + pixel[r, c-1]
        """
        height, width = diff_array.shape
        pixel_array = np.zeros((height, width), dtype=np.uint8)

        for r in range(height):
            for c in range(width):
                if c == 0:
                    # İlk pikseli fark dizisinde olduğu gibi al
                    pixel_array[r, c] = diff_array[r, c]
                else:
                    val = (diff_array[r, c] - self.offset) + pixel_array[r, c-1]
                    # 0..255 aralığına düşmesi beklenir
                    pixel_array[r, c] = val
        return pixel_array
