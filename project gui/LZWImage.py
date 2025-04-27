#!/usr/bin/env python3
import os
import math
import struct
import numpy as np
from PIL import Image

class LZWImageCoding:
    def __init__(self, filename, data_type):
        self.filename = filename      # Örneğin: 'lena_grayscale'
        self.data_type = data_type    # 'image'
        self.codelength = None

    def compress_image_file(self):
        # Çalışma dizinini al
        current_directory = os.path.dirname(os.path.realpath(__file__))
        # Giriş dosyasının yolunu oluştur (örneğin .png uzantılı)
        input_file = self.filename + '.png'
        input_path = os.path.join(current_directory, input_file)
        # Çıkış dosyası: .bin uzantılı sıkıştırılmış dosya
        output_file = self.filename + '.bin'
        output_path = os.path.join(current_directory, output_file)

        # Görüntüyü gri seviye olarak oku
        img = Image.open(input_path).convert('L')
        pixel_array = np.array(img)
        height, width = pixel_array.shape

        # 2D piksel matrisini 1D listeye dönüştür (satır satır)
        pixel_list = pixel_array.flatten().tolist()

        # LZW sıkıştırma: piksel listesi üzerinde uygulayın
        encoded_codes = self.encode(pixel_list)

        # Sıkıştırma işlemi sırasında sözlük genişledikçe codelength belirlenir
        # (encode metodunda self.codelength ayarlanır)

        # Kod listesini binary string'e dönüştür
        bit_string = self.int_list_to_binary_string(encoded_codes)
        # Padding ekle: bit string'in uzunluğunu 8'in katına tamamla;
        # ilk 8 bit, eklenen sıfır sayısını saklar.
        padded_bit_string = self.pad_encoded_data(bit_string)
        # Bit string'i byte array'e çevir
        byte_array = self.get_byte_array(padded_bit_string)

        # Dosyaya meta bilgileri yaz: width (4 byte), height (4 byte), codelength (2 byte)
        with open(output_path, 'wb') as f:
            f.write(struct.pack('>I', width))    # 4 byte: genişlik
            f.write(struct.pack('>I', height))   # 4 byte: yükseklik
            f.write(struct.pack('>H', self.codelength))  # 2 byte: code length
            f.write(byte_array)

        print(f"{input_file} is compressed into {output_file}.")
        print(f"Image Dimensions: {width} x {height}")
        original_size = width * height  # Ham piksel verisi boyutu (byte cinsinden)
        compressed_size = os.path.getsize(output_path)
        print(f"Uncompressed Size (raw pixels): {original_size} bytes")
        print(f"Compressed Size: {compressed_size} bytes")
        print(f"Compression Ratio: {compressed_size / original_size:.3f}")
        return output_path

    def encode(self, pixel_list):
        # Başlangıç sözlüğü: her piksel değeri (0-255) tek elemanlı tuple olarak
        dict_size = 256
        dictionary = { (i,): i for i in range(dict_size) }
        w = []
        result = []
        for pixel in pixel_list:
            w_plus = w + [pixel]
            key = tuple(w_plus)
            if key in dictionary:
                w = w_plus
            else:
                result.append(dictionary[tuple(w)])
                dictionary[key] = dict_size
                dict_size += 1
                w = [pixel]
        if w:
            result.append(dictionary[tuple(w)])
        # codelength, sözlüğün genişliğine göre ayarlanır
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
        header = format(extra_padding, '08b')
        padded = header + bitstring + ("0" * extra_padding)
        return padded

    def get_byte_array(self, padded_bitstring):
        if len(padded_bitstring) % 8 != 0:
            raise ValueError("Padded bitstring length is not a multiple of 8.")
        b_array = bytearray()
        for i in range(0, len(padded_bitstring), 8):
            byte = padded_bitstring[i:i+8]
            b_array.append(int(byte, 2))
        return b_array

    def decompress_image_file(self):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        input_file = self.filename + '.bin'
        input_path = os.path.join(current_directory, input_file)
        output_file = self.filename + '_decompressed.png'
        output_path = os.path.join(current_directory, output_file)

        with open(input_path, 'rb') as f:
            width = struct.unpack('>I', f.read(4))[0]
            height = struct.unpack('>I', f.read(4))[0]
            code_length = struct.unpack('>H', f.read(2))[0]
            compressed_bytes = f.read()

        # Byte array'den bit string oluştur
        bitstring = ""
        for byte in compressed_bytes:
            bitstring += format(byte, '08b')
        # İlk 8 bit: padding bilgisi
        extra_padding = int(bitstring[:8], 2)
        bitstring = bitstring[8:]
        if extra_padding > 0:
            bitstring = bitstring[:-extra_padding]

        # Bit string'i code_length'lık parçalara ayırarak integer kodlar listesi oluştur
        codes = []
        for i in range(0, len(bitstring), code_length):
            chunk = bitstring[i:i+code_length]
            if len(chunk) < code_length:
                break
            codes.append(int(chunk, 2))

        # LZW dekompresyon algoritması
        decompressed_pixels = self.decode(codes)
        # Listeyi 2D numpy array'e (yükseklik x genişlik) dönüştür
        pixel_array = np.array(decompressed_pixels, dtype=np.uint8).reshape((height, width))
        # Geri yüklenmiş görüntüyü kaydet
        img = Image.fromarray(pixel_array, 'L')
        img.save(output_path)

        print(f"{input_file} is decompressed into {output_file}.")
        return output_path

    def decode(self, codes):
        dict_size = 256
        dictionary = { i: [i] for i in range(dict_size) }
        w = dictionary[codes[0]]
        result = w[:]
        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code]
            elif code == dict_size:
                entry = w + [w[0]]
            else:
                raise ValueError("Bad compressed code: %s" % code)
            result.extend(entry)
            dictionary[dict_size] = w + [entry[0]]
            dict_size += 1
            w = entry
        return result
