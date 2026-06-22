import csv
import ast
import os

# --- VARIABEL PATH FILE ---
# Ubah nilai variabel ini sesuai dengan nama file Anda
INPUT_FILE_PATH = r"tweets\1000_Tweet\Merge_5152.csv"
OUTPUT_FILE_PATH = r"preprocesing\adjacency_list.csv"
# ---------------------------

# --- VARIABEL UNTUK FILTER GROK ---
GROK_HANDLE = "@grok" # Handle yang ingin difilter
# ----------------------------------

def is_grok_handle(handle: str) -> bool:
    """Memeriksa apakah handle adalah Grok (case-insensitive dan dengan/tanpa '@')."""
    if not isinstance(handle, str):
        return False
    # Mengabaikan perbedaan huruf besar/kecil dan menghapus '@' di awal (jika ada)
    normalized_handle = handle.strip().lower().lstrip('@')
    normalized_grok = GROK_HANDLE.lstrip('@')
    return normalized_handle == normalized_grok

def generate_gephi_network_csv(input_filename, output_filename):
    """
    Memproses file CSV mentah untuk menghasilkan file CSV format Source, Target
    yang dapat diimpor ke Gephi, tanpa menyertakan kolom 'Content'.
    Ditambahkan filter untuk mengecualikan tweet yang melibatkan akun Grok.
    """
    try:
        # 1. Pastikan direktori output ada
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 2. Membaca file input
        with open(input_filename, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile, delimiter=',')
            
            gephi_edges = []
            processed_tweet_ids = set() 
            total_rows_read = 0
            skipped_duplicates = 0
            skipped_grok_filter = 0 # Counter baru untuk filter Grok

            for row in reader:
                total_rows_read += 1
                try:
                    # Ambil Tweet ID 
                    tweet_id = row.get("Tweet ID", "").strip()
                    
                    # --- CEK DUPLIKAT ---
                    if not tweet_id:
                        continue 
                        
                    if tweet_id in processed_tweet_ids:
                        skipped_duplicates += 1
                        continue 
                    
                    processed_tweet_ids.add(tweet_id) 
                    # ----------------------
                    
                    # 1. Tentukan SOURCE (Pengirim Tweet/Post)
                    source_handle = row.get("Handle", "").strip().lstrip('@')

                    # Lewati jika Handle kosong setelah di-strip
                    if not source_handle:
                        continue
                        
                    # --- FILTER GROK PADA SOURCE ---
                    if is_grok_handle(source_handle):
                        skipped_grok_filter += 1
                        continue # Lewati baris ini jika Grok adalah pengirimnya
                    # -------------------------------
                    
                    # 2. Inisialisasi dan Ambil semua TARGET
                    all_targets = []
                    
                    # --- Penanganan Khusus untuk Mentions/Replying To ---
                    
                    # Ambil TARGET dari kolom 'Mentions'
                    mentions_str = row.get("Mentions")
                    if mentions_str and isinstance(mentions_str, str) and mentions_str.strip():
                        try:
                            mentions_list = ast.literal_eval(mentions_str)
                            if isinstance(mentions_list, (list, tuple)):
                                all_targets.extend(mentions_list)
                        except (ValueError, SyntaxError):
                            pass

                    # Ambil TARGET dari kolom 'Replying To'
                    replying_to_str = row.get("Replying To")
                    if replying_to_str and isinstance(replying_to_str, str) and replying_to_str.strip():
                        try:
                            replying_to_list = ast.literal_eval(replying_to_str)
                            if isinstance(replying_to_list, (list, tuple)):
                                all_targets.extend(replying_to_list)
                        except (ValueError, SyntaxError):
                            pass

                    # 3. Membuat EDGE untuk setiap Target unik
                    unique_targets = set(all_targets)
                    targets_to_process = []
                    
                    # --- FILTER GROK PADA TARGET SEBELUM MEMBUAT EDGE ---
                    # Hapus '@' dari target_with_at untuk pengecekan
                    for target_with_at in unique_targets:
                        # Pastikan target_with_at adalah string sebelum strip()
                        if not isinstance(target_with_at, str):
                            continue
                            
                        target_handle_stripped = target_with_at.strip().lstrip('@')
                        
                        # Cek apakah TARGET adalah Grok
                        if is_grok_handle(target_handle_stripped):
                            # Jika Target adalah Grok, hitung dan JANGAN tambahkan ke targets_to_process
                            # Walaupun tweetnya bukan dari grok, kita hilangkan *edge* ke grok
                            skipped_grok_filter += 1 
                        else:
                            targets_to_process.append(target_handle_stripped)
                    # ----------------------------------------------------

                    for target_handle in targets_to_process:
                        # Pastikan Source dan Target valid dan berbeda (pengecekan lower-case)
                        if source_handle and target_handle and source_handle.lower() != target_handle.lower():
                            gephi_edges.append([source_handle, target_handle]) 

                except (KeyError, ValueError, IndexError, SyntaxError, AttributeError, TypeError) as e:
                    # Melewatkan baris yang rusak atau tidak lengkap
                    print(f"Skipping row {total_rows_read} due to error: {type(e).__name__} - {e}")
                    continue

        # 4. Menulis hasil ke file CSV output
        with open(output_filename, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL) 
            
            # Hanya menulis header "Source" dan "Target"
            writer.writerow(["Source", "Target"]) 
            writer.writerows(gephi_edges)

        print(f"\n--- RINGKASAN PEMROSESAN ---")
        print(f"File input: '{input_filename}'")
        print(f"Total baris dibaca: {total_rows_read}")
        print(f"Total ID Tweet unik diproses: {len(processed_tweet_ids)}")
        print(f"Baris duplikat diabaikan: {skipped_duplicates}")
        print(f"Baris/Edge yang melibatkan '{GROK_HANDLE}' diabaikan: {skipped_grok_filter}") # Ringkasan baru
        print(f"Total edge (tepi) ditulis ke file Gephi: {len(gephi_edges)}")
        print(f"Pembuatan file Gephi berhasil! File output: '{output_filename}' (Hanya Source dan Target)")

    except FileNotFoundError:
        print(f"ERROR: File input '{input_filename}' tidak ditemukan. Pastikan nama filenya sudah benar.")
    except Exception as e:
        print(f"Terjadi error tak terduga: {e}")

# --- EKSEKUSI SKRIP ---
generate_gephi_network_csv(
    input_filename=INPUT_FILE_PATH, 
    output_filename=OUTPUT_FILE_PATH
)