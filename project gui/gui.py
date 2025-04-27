import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import shutil
from PIL import Image

# Ana pencere oluşturma
root = tk.Tk()
root.title("LZW Compression GUI")

# ------------------ DOSYA SEÇME ALANI ------------------
file_frame = tk.Frame(root)
file_frame.pack(pady=10)

tk.Label(file_frame, text="Input File:").pack(side=tk.LEFT)

file_entry = tk.Entry(file_frame, width=50)
file_entry.pack(side=tk.LEFT, padx=5)

def browse_file():
    """Dosya seçme fonksiyonu (Browse butonuyla çağrılır)."""
    filepath = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
    if filepath:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, filepath)

tk.Button(file_frame, text="Browse", command=browse_file).pack(side=tk.LEFT)

# ------------------ METOD SEÇİMİ (Level 1-5) ------------------
method_var = tk.StringVar(root)
method_var.set("Text Compression (Level 1)")

method_options = [
    "Text Compression (Level 1)",
    "Gray Level Image Compression (Level 2)",
    "Gray Level Difference Compression (Level 3)",
    "Color Image Compression (Level 4)",
    "Color Differences Compression (Level 5)"
]

tk.Label(root, text="Select Compression Method:").pack()
method_menu = tk.OptionMenu(root, method_var, *method_options)
method_menu.pack(pady=5)

# ------------------ BUTONLAR (Compress / Decompress) ------------------
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# ------------------ ÇIKTI ALANI (ScrolledText) ------------------
output_text = scrolledtext.ScrolledText(root, width=80, height=20)
output_text.pack(pady=10)

# Çıktılar için klasörleri hazırla
project_dir = os.path.dirname(os.path.abspath(__file__))
compressed_dir = os.path.join(project_dir, "compressed")
decompressed_dir = os.path.join(project_dir, "decompressed")
os.makedirs(compressed_dir, exist_ok=True)
os.makedirs(decompressed_dir, exist_ok=True)

def compress_file():
    """Seçili yöntem ve dosya için sıkıştırma işlemini yapan fonksiyon."""
    filepath = file_entry.get()
    if not filepath:
        messagebox.showerror("Error", "Please select an input file!")
        return

    method = method_var.get()
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    ext = os.path.splitext(filepath)[1].lower()
    file_dir = os.path.dirname(filepath)

    output_text.insert(tk.END, f"[INFO] Compressing '{filepath}' with '{method}'\n")
    try:
        if method == "Text Compression (Level 1)":
            # Girdi metnini proje dizinine .txt uzantısıyla kopyala (gerekiyorsa)
            dest_input = filepath
            if ext != ".txt" or file_dir != project_dir:
                dest_input = os.path.join(project_dir, base_name + ".txt")
                shutil.copy(filepath, dest_input)
            from LZW import LZWCoding
            compressor = LZWCoding(base_name, "text")
            out_path = compressor.compress_text_file()
            # Sıkıştırılmış dosyayı 'compressed' klasörüne taşı
            if out_path and os.path.exists(out_path):
                final_path = os.path.join(compressed_dir, os.path.basename(out_path))
                shutil.move(out_path, final_path)
                out_path = final_path
            else:
                raise FileNotFoundError("Compressed output not found.")
            # Geçici kopyalanan dosyayı sil
            if dest_input != filepath and os.path.exists(dest_input):
                os.remove(dest_input)

        elif method == "Gray Level Image Compression (Level 2)":
            # Gri seviye görüntüyü proje dizinine .png olarak kopyala/dönüştür
            dest_input = filepath
            if ext != ".png" or file_dir != project_dir:
                dest_input = os.path.join(project_dir, base_name + ".png")
                try:
                    img = Image.open(filepath)
                    img = img.convert('L')  # Gri formata çevir
                    img.save(dest_input)
                    img.close()
                except Exception as e:
                    raise RuntimeError(f"Failed to prepare image for compression: {e}")
            from LZWImage import LZWImageCoding
            compressor = LZWImageCoding(base_name, "image")
            out_path = compressor.compress_image_file()
            if out_path and os.path.exists(out_path):
                final_path = os.path.join(compressed_dir, os.path.basename(out_path))
                shutil.move(out_path, final_path)
                out_path = final_path
            else:
                raise FileNotFoundError("Compressed output not found.")
            if dest_input != filepath and os.path.exists(dest_input):
                os.remove(dest_input)

        elif method == "Gray Level Difference Compression (Level 3)":
            # Gri seviye fark görüntüsünü proje dizinine .png olarak hazırla
            dest_input = filepath
            if ext != ".png" or file_dir != project_dir:
                dest_input = os.path.join(project_dir, base_name + ".png")
                try:
                    img = Image.open(filepath)
                    img = img.convert('L')
                    img.save(dest_input)
                    img.close()
                except Exception as e:
                    raise RuntimeError(f"Failed to prepare image for compression: {e}")
            from LZWImageDiff import LZWImageDiffCoding
            compressor = LZWImageDiffCoding(base_name, "image")
            out_path = compressor.compress_image_file()
            if out_path and os.path.exists(out_path):
                final_path = os.path.join(compressed_dir, os.path.basename(out_path))
                shutil.move(out_path, final_path)
                out_path = final_path
            else:
                raise FileNotFoundError("Compressed output not found.")
            if dest_input != filepath and os.path.exists(dest_input):
                os.remove(dest_input)

        elif method == "Color Image Compression (Level 4)":
            # Renkli görüntüyü proje dizinine .png (RGB) olarak hazırla
            dest_input = filepath
            actual_base = base_name  # Sınıfa verilecek dosya adı gövdesi
            if ext != ".png" or file_dir != project_dir:
                dest_input = os.path.join(project_dir, base_name + ".png")
                try:
                    img = Image.open(filepath)
                    img = img.convert('RGB')
                    img.save(dest_input)
                    img.close()
                except Exception as e:
                    raise RuntimeError(f"Failed to prepare image for compression: {e}")
            else:
                # Dosya zaten .png ise, 3 kanallı olduğundan emin ol
                img = Image.open(filepath)
                if img.mode != 'RGB':
                    dest_input = os.path.join(project_dir, base_name + "_rgb.png")
                    img = img.convert('RGB')
                    img.save(dest_input)
                    actual_base = base_name + "_rgb"
                img.close()
            from LZWColor import LZWColorCoding
            compressor = LZWColorCoding(actual_base, "image")
            out_path = compressor.compress_image_file()
            # Eğer çıktı yolu dönmediyse veya dosya yoksa tahmin et
            if not out_path or not os.path.exists(out_path):
                guess_path = os.path.join(project_dir, actual_base + ".bin")
                if os.path.exists(guess_path):
                    out_path = guess_path
                else:
                    raise FileNotFoundError("Compressed output not found.")
            # Sıkıştırılmış dosyayı 'compressed' klasörüne taşı
            final_path = os.path.join(compressed_dir, os.path.basename(out_path))
            shutil.move(out_path, final_path)
            out_path = final_path
            if dest_input != filepath and os.path.exists(dest_input):
                os.remove(dest_input)

        elif method == "Color Differences Compression (Level 5)":
            # Renkli 2D fark görüntüsünü proje dizinine .png (RGB) olarak hazırla
            dest_input = filepath
            actual_base = base_name
            if ext != ".png" or file_dir != project_dir:
                dest_input = os.path.join(project_dir, base_name + ".png")
                try:
                    img = Image.open(filepath)
                    img = img.convert('RGB')
                    img.save(dest_input)
                    img.close()
                except Exception as e:
                    raise RuntimeError(f"Failed to prepare image for compression: {e}")
            else:
                img = Image.open(filepath)
                if img.mode != 'RGB':
                    dest_input = os.path.join(project_dir, base_name + "_rgb.png")
                    img = img.convert('RGB')
                    img.save(dest_input)
                    actual_base = base_name + "_rgb"
                img.close()
            from LZWColor2DDiff import LZWColor2DDiffCoding
            compressor = LZWColor2DDiffCoding(actual_base, "image")
            out_path = compressor.compress_image_file()
            # Eğer çıktı yolu dönmediyse veya dosya yoksa tahmin et
            if not out_path or not os.path.exists(out_path):
                guess_path = os.path.join(project_dir, actual_base + ".bin")
                if os.path.exists(guess_path):
                    out_path = guess_path
                else:
                    raise FileNotFoundError("Compressed output not found.")
            # Sıkıştırılmış dosyayı 'compressed' klasörüne taşı
            final_path = os.path.join(compressed_dir, os.path.basename(out_path))
            shutil.move(out_path, final_path)
            out_path = final_path
            if dest_input != filepath and os.path.exists(dest_input):
                os.remove(dest_input)

        else:
            messagebox.showerror("Error", f"Unknown method: {method}")
            return

        output_text.insert(tk.END, f"Compression complete!\nOutput: {out_path}\n\n")
    except Exception as e:
        messagebox.showerror("Compression Error", str(e))
        output_text.insert(tk.END, f"[ERROR] Compression failed: {e}\n\n")

def decompress_file():
    """Seçili yöntem ve dosya için açma (decompression) işlemini yapan fonksiyon."""
    filepath = file_entry.get()
    if not filepath:
        messagebox.showerror("Error", "Please select an input file!")
        return

    method = method_var.get()
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    ext = os.path.splitext(filepath)[1].lower()
    file_dir = os.path.dirname(filepath)

    output_text.insert(tk.END, f"[INFO] Decompressing '{filepath}' with '{method}'\n")

    # Yalnızca .bin dosyaları açabiliriz, uzantıyı kontrol et
    if ext != ".bin":
        messagebox.showerror("Error", "Please select a .bin file for decompression!")
        return

    try:
        # .bin dosyasını proje dizinine kopyala (gerekiyorsa)
        temp_bin_path = None
        if file_dir != project_dir:
            temp_bin_path = os.path.join(project_dir, os.path.basename(filepath))
            shutil.copy(filepath, temp_bin_path)
        # Seçilen seviyeye göre uygun LZW sınıfını kullanarak açma
        if method == "Text Compression (Level 1)":
            from LZW import LZWCoding
            decompressor = LZWCoding(base_name, "text")
            out_path = decompressor.decompress_text_file()
        elif method == "Gray Level Image Compression (Level 2)":
            from LZWImage import LZWImageCoding
            decompressor = LZWImageCoding(base_name, "image")
            out_path = decompressor.decompress_image_file()
        elif method == "Gray Level Difference Compression (Level 3)":
            from LZWImageDiff import LZWImageDiffCoding
            decompressor = LZWImageDiffCoding(base_name, "image")
            out_path = decompressor.decompress_image_file()
        elif method == "Color Image Compression (Level 4)":
            from LZWColor import LZWColorCoding
            decompressor = LZWColorCoding(base_name, "image")
            out_path = decompressor.decompress_image_file()
        elif method == "Color Differences Compression (Level 5)":
            from LZWColor2DDiff import LZWColor2DDiffCoding
            decompressor = LZWColor2DDiffCoding(base_name, "image")
            out_path = decompressor.decompress_image_file()
        else:
            messagebox.showerror("Error", f"Unknown method: {method}")
            # Temizle ve çık
            if temp_bin_path and os.path.exists(temp_bin_path):
                os.remove(temp_bin_path)
            return

        # Sınıfın döndürdüğü çıktı yoksa (renkli sıkıştırmalarda None dönüyordu), tahmin et
        if not out_path or not os.path.exists(out_path):
            expected_ext = ".txt" if method.startswith("Text") else ".png"
            guess_path = os.path.join(project_dir, base_name + "_decompressed" + expected_ext)
            if os.path.exists(guess_path):
                out_path = guess_path
            else:
                raise FileNotFoundError("Decompressed output file not found.")

        # Açılmış dosyayı 'decompressed' klasörüne taşı
        final_path = os.path.join(decompressed_dir, os.path.basename(out_path))
        shutil.move(out_path, final_path)
        out_path = final_path

        # Geçici kopyalanan .bin dosyasını sil
        if temp_bin_path and os.path.exists(temp_bin_path):
            os.remove(temp_bin_path)

        output_text.insert(tk.END, f"Decompression complete!\nOutput: {out_path}\n\n")
    except Exception as e:
        messagebox.showerror("Decompression Error", str(e))
        output_text.insert(tk.END, f"[ERROR] Decompression failed: {e}\n\n")
        # Hata durumunda geçici dosya kalmışsa sil
        if 'temp_bin_path' in locals() and temp_bin_path and os.path.exists(temp_bin_path):
            os.remove(temp_bin_path)

# Compress / Decompress butonlarını oluştur ve yerleştir
tk.Button(button_frame, text="Compress", command=compress_file).pack(side=tk.LEFT, padx=10)
tk.Button(button_frame, text="Decompress", command=decompress_file).pack(side=tk.LEFT, padx=10)

# Tkinter döngüsünü başlat
root.mainloop()
