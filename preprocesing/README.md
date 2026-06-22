## Preprocessing
File `raw_to_adjency_list.py` dibuat untuk mengubah hasil scraping menjadi **adjacency list** (`Source`, `Target`) yang siap diimpor ke Gephi untuk analisis jaringan.

| Atribut       | Peran  | Keterangan                    |
| ------------- | ------ | ----------------------------- |
| `Handle`      | Source | Akun yang membuat tweet       |
| `Mentions`    | Target | Akun yang disebut dalam tweet |
| `Replying To` | Target | Akun yang menerima balasan    |

Data duplikat, self-loop (`Source = Target`), dan interaksi yang melibatkan **@grok** akan dihapus selama proses preprocessing.


## Gephi Files and Visulaization
file menatah `Ready_To_Import.csv` di import ke Gephi untuk analisis lanjutan.

Untuk file `final_data.gephi` adalah data yg sudah di analisis seperti Sentralitas(degree, betweenes, closeness dll). 
> `final_data.gephi` bisa diimport langsung ke gephi

Untuk file `data_exported_from_gephi.csv` adalah data untuk hasil nilai setiap metrik sentralitas dan yg lainnya. Ini dibuat agar bisa memvisualisasikan ulang secara jelas dengan kode dari file `data_gephi_revisualization.py`