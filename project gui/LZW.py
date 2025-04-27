import os  # the os module is used for file and directory operations
import math  # the math module provides access to mathematical functions

# A class that implements the LZW compression and decompression algorithms as
# well as the necessary utility methods for text files.
# ------------------------------------------------------------------------------
class LZWCoding:
   # A constructor with two input parameters
   # ---------------------------------------------------------------------------
   def __init__(self, filename, data_type):
      # use the input parameters to set the instance variables
      self.filename = filename
      self.data_type = data_type   # e.g., 'text'
      # initialize the code length as None 
      # (the actual value is determined based on the compressed data)
      self.codelength = None

   # A method that compresses the contents of a text file to a binary output file 
   # and returns the path of the output file.
   # ---------------------------------------------------------------------------
   def compress_text_file(self):
      # get the current directory where this program is placed
      current_directory = os.path.dirname(os.path.realpath(__file__))
      # build the path of the input file
      input_file = self.filename + '.txt'
      input_path = current_directory + '/' + input_file
      # build the path of the output file
      output_file = self.filename + '.bin'
      output_path = current_directory + '/' + output_file

      # read the contents of the input file
      in_file = open(input_path, 'r')
      text = in_file.read().rstrip()
      in_file.close()

      # encode the text by using the LZW compression algorithm
      encoded_text_as_integers = self.encode(text)
      # get the binary string that corresponds to the compressed text
      encoded_text = self.int_list_to_binary_string(encoded_text_as_integers)
      # add the code length info to the beginning of the encoded text
      encoded_text = self.add_code_length_info(encoded_text)
      # perform padding if needed
      padded_encoded_text = self.pad_encoded_data(encoded_text)
      # convert the resulting string into a byte array
      byte_array = self.get_byte_array(padded_encoded_text)

      # write the bytes in the byte array to the output file (compressed file)
      out_file = open(output_path, 'wb')   # binary mode
      out_file.write(bytes(byte_array))
      out_file.close()

      # notify the user that the compression process is finished
      print(input_file + ' is compressed into ' + output_file + '.')
      # compute and print the details of the compression process
      uncompressed_size = len(text)
      print('Uncompressed Size: ' + '{:,d}'.format(uncompressed_size) + ' bytes')
      print('Code Length: ' + str(self.codelength))
      compressed_size = len(byte_array)
      print('Compressed Size: ' + '{:,d}'.format(compressed_size) + ' bytes')
      compression_ratio = uncompressed_size / compressed_size
      print('Compression Ratio: ' + '{:.2f}'.format(compression_ratio))

      # return the path of the output file
      return output_path
   
   # A method that encodes a text input into a list of integer values by using
   # the LZW compression algorithm and returns the resulting list.
   # ---------------------------------------------------------------------------
   def encode(self, uncompressed_data):
      # build the initial dictionary by mapping the characters in the extended 
      # ASCII table to their indexes
      dict_size = 256
      dictionary = {chr(i): i for i in range(dict_size)}

      # perform the LZW compression algorithm
      w = ''   # initialize a variable to store the current sequence
      result = []   # initialize a list to store the encoded values to output
      # iterate over each item (a character for text files) in the input data
      for k in uncompressed_data:
         # keep forming a new sequence until it is not in the dictionary
         wk = w + k
         if wk in dictionary:   # if wk exists in the dictionary
            w = wk   # update the sequence by adding the current item
         else:   # otherwise
            # add the code for w (the longest sequence found in the dictionary)
            # to the list that stores the encoded values
            result.append(dictionary[w])
            # add wk (the new sequence) to the dictionary
            dictionary[wk] = dict_size
            dict_size += 1
            # reset w to the current character
            w = k
      # add the code for the remaining sequence (if it exists) to the list that 
      # stores the encoded values (integer codes)
      if w:
         result.append(dictionary[w])
      
      # set the code length for compressing the encoded values based on the input 
      # data (by using the size of the resulting dictionary)
      self.codelength = math.ceil(math.log2(len(dictionary)))

      # return the encoded values (a list of integer dictionary values)
      return result

   # A method that converts the integer list returned by the compress method
   # into a binary string and returns the resulting string.
   # ---------------------------------------------------------------------------
   def int_list_to_binary_string(self, int_list):
      # initialize the binary string as an empty string
      bitstring = ''
      # concatenate each integer in the input list to the binary string
      for num in int_list:
         # using codelength bits to compress each value
         for n in range(self.codelength):
            if num & (1 << (self.codelength - 1 - n)):
               bitstring += '1'
            else:
               bitstring += '0'
      # return the resulting binary string
      return bitstring

   # A method that adds the code length to the beginning of the binary string
   # that corresponds to the compressed data and returns the resulting string.
   # (the compressed data should contain everything needed to decompress it)
   # ---------------------------------------------------------------------------
   def add_code_length_info(self, bitstring):
      # create a binary string that stores the code length as a byte
      codelength_info = '{0:08b}'.format(self.codelength)
      # add the code length info to the beginning of the given binary string
      bitstring = codelength_info + bitstring
      # return the resulting binary string
      return bitstring

   # A method for adding zeros to the binary string (the compressed data)
   # to make the length of the string a multiple of 8.
   # (This is necessary to be able to write the values to the file as bytes.)
   # ---------------------------------------------------------------------------
   def pad_encoded_data(self, encoded_data):
      # compute the number of the extra bits to add
      if len(encoded_data) % 8 != 0:
         extra_bits = 8 - len(encoded_data) % 8
         # add zeros to the end (padding)
         for i in range(extra_bits):
            encoded_data += '0'
      else:   # no need to add zeros
         extra_bits = 0
      # add a byte that stores the number of added zeros to the beginning of
      # the encoded data
      padding_info = '{0:08b}'.format(extra_bits)
      encoded_data = padding_info + encoded_data
      # return the resulting string after padding
      return encoded_data

   # A method that converts the padded binary string to a byte array and returns 
   # the resulting array. 
   # (This byte array will be written to a file to store the compressed data.)
   # ---------------------------------------------------------------------------
   def get_byte_array(self, padded_encoded_data):
      # the length of the padded binary string must be a multiple of 8
      if (len(padded_encoded_data) % 8 != 0):
         print('The compressed data is not padded properly!')
         exit(0)
      # create a byte array
      b = bytearray()
      # append the padded binary string to byte by byte
      for i in range(0, len(padded_encoded_data), 8):
         byte = padded_encoded_data[i : i + 8]
         b.append(int(byte, 2))
      # return the resulting byte array
      return b

   # A method that reads the contents of a compressed binary file, performs
   # decompression and writes the decompressed output to a text file.
   # ---------------------------------------------------------------------------
   def decompress_text_file(self):
      # get the current directory where this program is placed
      current_directory = os.path.dirname(os.path.realpath(__file__))
      # build the path of the input file
      input_file = self.filename + '.bin'
      input_path = current_directory + '/' + input_file
      # build the path of the output file
      output_file = self.filename + '_decompressed.txt'
      output_path = current_directory + '/' + output_file

      # read the contents of the input file
      in_file = open(input_path, 'rb')   # binary mode
      bytes = in_file.read()
      in_file.close()

      # create a binary string from the bytes read from the file
      from io import StringIO   # using StringIO for efficiency
      bit_string = StringIO()
      for byte in bytes:
         bits = bin(byte)[2:].rjust(8, '0')
         bit_string.write(bits)
      bit_string = bit_string.getvalue()

      # remove padding
      bit_string = self.remove_padding(bit_string)
      # remove the code length info and set the instance variable codelength
      bit_string = self.extract_code_length_info(bit_string)
      # convert the compressed binary string to a list of integer values
      encoded_text = self.binary_string_to_int_list(bit_string)
      # decode the encoded text by using the LZW decompression algorithm
      decompressed_text = self.decode(encoded_text)

      # write the decompression output to the output file
      out_file = open(output_path, 'w')
      out_file.write(decompressed_text)
      out_file.close()

      # notify the user that the decompression process is finished
      print(input_file + ' is decompressed into ' + output_file + '.')
      
      # return the path of the output file
      return output_path

   # A method to remove the padding info and the added zeros from the compressed
   # binary string and return the resulting string.
   def remove_padding(self, padded_encoded_data):
      # extract the padding info (the first 8 bits of the input string)
      padding_info = padded_encoded_data[:8]
      encoded_data = padded_encoded_data[8:]
      # remove the extra zeros (if any) and return the resulting string
      extra_padding = int(padding_info, 2) 
      if extra_padding != 0:
         encoded_data = encoded_data[:-1 * extra_padding]
      return encoded_data

   # A method to extract the code length info from the compressed binary string
   # and return the resulting string.
   # ---------------------------------------------------------------------------
   def extract_code_length_info(self, bitstring):
      # the first 8 bits of the input string contains the code length info
      codelength_info = bitstring[:8]
      self.codelength = int(codelength_info, 2)
      # return the resulting binary string after removing the code length info
      return bitstring[8:]

   # A method that converts the compressed binary string to a list of int codes
   # and returns the resulting list.
   # ---------------------------------------------------------------------------
   def binary_string_to_int_list(self, bitstring):
      # generate the list of integer codes from the binary string
      int_codes = []
      # for each compressed value (a binary string with codelength bits)
      for bits in range(0, len(bitstring), self.codelength):
         # compute the integer code and add it to the list
         int_code = int(bitstring[bits: bits + self.codelength], 2)
         int_codes.append(int_code)
      # return the resulting list
      return int_codes
   
   # A method that decodes a list of encoded integer values into a string (text) 
   # by using the LZW decompression algorithm and returns the resulting output.
   # ---------------------------------------------------------------------------
   def decode(self, encoded_values):
      # build the initial dictionary by mapping the index values in the extended 
      # ASCII table to their corresponding characters
      dict_size = 256
      dictionary = {i: chr(i) for i in range(dict_size)}

      # perform the LZW decompression algorithm
      # ------------------------------------------------------------------------
      from io import StringIO   # using StringIO for efficiency
      result = StringIO()
      # initialize w as the character corresponding to the first encoded value
      # in the list and add this character to the output string
      w = chr(encoded_values.pop(0))
      result.write(w)
      # iterate over each encoded value in the list
      for k in encoded_values:
         # if the value is in the dictionary
         if k in dictionary:
            # retrieve the corresponding string
            entry = dictionary[k]
         # if the value is equal to the current dictionary size
         elif k == dict_size:
            # construct the entry
            entry = w + w[0]   # a special case where the entry is formed
         # if k is invalid (not in the dictionary and not equal to dict_size)
         else:
            # raise an error
            raise ValueError('Bad compressed k: %s' % k)
         # add the entry to the output
         result.write(entry)
         # w + the first character of the entry is added to the dictionary 
         # as a new sequence
         dictionary[dict_size] = w + entry[0]
         dict_size += 1
         # update w to the current entry
         w = entry
      
      # return the resulting output (the decompressed string/text)
      return result.getvalue()
