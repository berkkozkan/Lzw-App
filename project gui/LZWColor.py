#!/usr/bin/env python3
import os
import math
import struct
import numpy as np
from PIL import Image

class LZWColorCoding:
    def __init__(self, filename, data_type):
        """
        Basit LZW tabanlı renkli (RGB) görüntü sıkıştırma/açma sınıfı.
        filename: giriş/çıkış dosya adı gövdesi (ör. 'lena_color')
        data_type: 'image' vb.
        """
        self.filename = filename
        self.data_type = data_type
        # Her kanal için ayrı code length tutabiliriz
        self.code_length_R = None
        self.code_length_G = None
        self.code_length_B = None

    def compress_image_file(self):
        """
        1) Renkli görüntüyü oku (R, G, B)
        2) Her kanalı (R, G, B) ayrı ayrı LZW sıkıştır
        3) Her kanal için code_length hesapla
        4) Tek bir .bin dosyasına meta bilgi + sıkıştırılmış veriyi yaz
        """
        current_directory = os.path.dirname(os.path.realpath(__file__))
        input_file = self.filename + '.png'   # örnek uzantı
        input_path = os.path.join(current_directory, input_file)
        output_file = self.filename + '.bin'
        output_path = os.path.join(current_directory, output_file)

        # 1) Renkli görüntüyü oku
        img = Image.open(input_path).convert('RGB')  # 3 kanal (R, G, B)
        pixel_array = np.array(img)
        height, width, channels = pixel_array.shape  # channels = 3

        # Ayrı kanallara ayır (R, G, B)
        R_channel = pixel_array[..., 0].flatten().tolist()
        G_channel = pixel_array[..., 1].flatten().tolist()
        B_channel = pixel_array[..., 2].flatten().tolist()

        # 2) Her kanalı LZW ile sıkıştır
        encoded_R, dict_size_R = self.encode_channel(R_channel)
        encoded_G, dict_size_G = self.encode_channel(G_channel)
        encoded_B, dict_size_B = self.encode_channel(B_channel)

        # 3) code_length hesapla
        self.code_length_R = math.ceil(math.log2(dict_size_R))
        self.code_length_G = math.ceil(math.log2(dict_size_G))
        self.code_length_B = math.ceil(math.log2(dict_size_B))

        # 4) Kodları bit string'e çevirip padding ekle
        bitstring_R = self.int_list_to_bitstring(encoded_R, self.code_length_R)
        padded_R, extra_pad_R = self.pad_bitstring(bitstring_R)
        byte_array_R = self.bitstring_to_byte_array(padded_R)

        bitstring_G = self.int_list_to_bitstring(encoded_G, self.code_length_G)
        padded_G, extra_pad_G = self.pad_bitstring(bitstring_G)
        byte_array_G = self.bitstring_to_byte_array(padded_G)

        bitstring_B = self.int_list_to_bitstring(encoded_B, self.code_length_B)
        padded_B, extra_pad_B = self.pad_bitstring(bitstring_B)
        byte_array_B = self.bitstring_to_byte_array(padded_B)

        # Dosyaya yazacağımız format (basit bir örnek):
        # width (4 byte), height (4 byte)
        # code_length_R (2 byte), extra_pad_R (1 byte), R data length (4 byte), R data
        # code_length_G (2 byte), extra_pad_G (1 byte), G data length (4 byte), G data
        # code_length_B (2 byte), extra_pad_B (1 byte), B data length (4 byte), B data
        with open(output_path, 'wb') as f:
            # width, height
            f.write(struct.pack('>I', width))
            f.write(struct.pack('>I', height))

            # R meta
            f.write(struct.pack('>H', self.code_length_R))  # 2 byte
            f.write(struct.pack('>B', extra_pad_R))         # 1 byte (R padding)
            f.write(struct.pack('>I', len(byte_array_R)))   # 4 byte (R data uzunluğu)
            f.write(byte_array_R)

            # G meta
            f.write(struct.pack('>H', self.code_length_G))
            f.write(struct.pack('>B', extra_pad_G))
            f.write(struct.pack('>I', len(byte_array_G)))
            f.write(byte_array_G)

            # B meta
            f.write(struct.pack('>H', self.code_length_B))
            f.write(struct.pack('>B', extra_pad_B))
            f.write(struct.pack('>I', len(byte_array_B)))
            f.write(byte_array_B)

        # Sıkıştırma oranı hesaplama (isteğe bağlı)
        original_size = width * height * 3  # her piksel 3 byte (RGB)
        compressed_size = os.path.getsize(output_path)
        print(f"{input_file} is compressed into {output_file}.")
        print(f"Original pixel count (3 channels): {original_size} bytes")
        print(f"Compressed file size: {compressed_size} bytes")
        if original_size != 0:
            ratio = compressed_size / original_size
            print(f"Compression Ratio: {ratio:.3f}")

    def encode_channel(self, channel_data):
        """
        channel_data: 0..255 aralığında int list (örneğin R kanalının piksel değerleri).
        return: (encoded_list, dict_size)
        """
        dict_size = 256
        dictionary = { (i,): i for i in range(dict_size) }

        w = []
        encoded = []
        for val in channel_data:
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
        """
        Her integer kodu code_length bitlik string'e çevirip birleştirir.
        """
        bitstring = ""
        for c in codes:
            bitstring += format(c, f'0{code_length}b')
        return bitstring

    def pad_bitstring(self, bitstring):
        """
        bitstring uzunluğu 8'in katı değilse padding ekler.
        extra_padding'i 1 byte olarak döndürüyoruz.
        """
        extra_padding = (8 - len(bitstring) % 8) % 8
        padded = bitstring + ('0' * extra_padding)
        return padded, extra_padding

    def bitstring_to_byte_array(self, bitstring):
        if len(bitstring) % 8 != 0:
            raise ValueError("Bitstring length is not multiple of 8.")
        b_arr = bytearray()
        for i in range(0, len(bitstring), 8):
            chunk = bitstring[i:i+8]
            b_arr.append(int(chunk, 2))
        return b_arr

    def decompress_image_file(self):
        """
        1) .bin dosyasını aç
        2) width, height oku
        3) Her kanalın meta bilgilerini ve verisini oku
        4) LZW decode ile R, G, B piksel dizilerini geri al
        5) R, G, B kanallarını birleştirerek renkli görüntü oluştur
        6) .png dosyasına kaydet
        """
        current_directory = os.path.dirname(os.path.realpath(__file__))
        input_file = self.filename + '.bin'
        input_path = os.path.join(current_directory, input_file)
        output_file = self.filename + '_decompressed.png'
        output_path = os.path.join(current_directory, output_file)

        with open(input_path, 'rb') as f:
            # width, height
            width = struct.unpack('>I', f.read(4))[0]
            height = struct.unpack('>I', f.read(4))[0]

            # R meta
            self.code_length_R = struct.unpack('>H', f.read(2))[0]
            extra_pad_R = struct.unpack('>B', f.read(1))[0]
            length_R = struct.unpack('>I', f.read(4))[0]
            data_R = f.read(length_R)

            # G meta
            self.code_length_G = struct.unpack('>H', f.read(2))[0]
            extra_pad_G = struct.unpack('>B', f.read(1))[0]
            length_G = struct.unpack('>I', f.read(4))[0]
            data_G = f.read(length_G)

            # B meta
            self.code_length_B = struct.unpack('>H', f.read(2))[0]
            extra_pad_B = struct.unpack('>B', f.read(1))[0]
            length_B = struct.unpack('>I', f.read(4))[0]
            data_B = f.read(length_B)

        # Her kanal için bitstring'e çevir, padding çıkar, kod listesine dön
        R_channel = self.decompress_channel(data_R, self.code_length_R, extra_pad_R)
        G_channel = self.decompress_channel(data_G, self.code_length_G, extra_pad_G)
        B_channel = self.decompress_channel(data_B, self.code_length_B, extra_pad_B)

        # Her kanaldaki piksel sayısı = width * height olmalı
        if len(R_channel) != width * height or len(G_channel) != width * height or len(B_channel) != width * height:
            raise ValueError("Decoded channel sizes do not match width*height.")

        # 2D matrislere dönüştür
        R_arr = np.array(R_channel, dtype=np.uint8).reshape((height, width))
        G_arr = np.array(G_channel, dtype=np.uint8).reshape((height, width))
        B_arr = np.array(B_channel, dtype=np.uint8).reshape((height, width))

        # Üç kanalı birleştirerek renkli görüntü oluştur
        color_array = np.dstack((R_arr, G_arr, B_arr))

        # Görüntüyü kaydet
        img = Image.fromarray(color_array, 'RGB')
        img.save(output_file)

        print(f"{input_file} is decompressed into {output_file}.")

    def decompress_channel(self, byte_data, code_length, extra_pad):
        """
        1) byte_data -> bitstring
        2) extra_pad kadar bit sonundan sil
        3) bitstring'i code_length parçalarına ayırıp integer kod listesi oluştur
        4) LZW decode
        5) piksel dizisi (0..255) döndür
        """
        bitstring = ""
        for b in byte_data:
            bitstring += format(b, '08b')

        # Padding çıkar
        if extra_pad > 0:
            bitstring = bitstring[:-extra_pad]

        # Kod listesi
        codes = []
        for i in range(0, len(bitstring), code_length):
            chunk = bitstring[i:i+code_length]
            if len(chunk) < code_length:
                break
            val = int(chunk, 2)
            codes.append(val)

        # LZW decode
        channel_data = self.decode_channel(codes)
        return channel_data

    def decode_channel(self, codes):
        """
        LZW dekompresyon. codes: integer list
        return: piksel list (0..255)
        """
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
