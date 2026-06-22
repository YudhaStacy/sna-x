import os
import pandas as pd
import matplotlib.pyplot as plt

# Membaca file CSV
df = pd.read_csv(r'preprocesing\data_exported_from_gephi.csv', sep=';')

# Folder output
output_dir = r'preprocesing\img'
os.makedirs(output_dir, exist_ok=True)

# Degree metrics
degree_metrics = {
    'Degree': 'Degree Distribution',
    'indegree': 'In-Degree Distribution',
    'outdegree': 'Out-Degree Distribution'
}

# Centrality metrics
centrality_metrics = {
    'betweenesscentrality': 'Betweenness Centrality Distribution',
    'closnesscentrality': 'Closeness Centrality Distribution',
    'eigencentrality': 'Eigenvector Centrality Distribution'
}

# Gabungkan semua metric
all_metrics = {**degree_metrics, **centrality_metrics}

for col, title_text in all_metrics.items():

    # Hitung distribusi
    counts = df[col].value_counts().sort_index()
    x = counts.index
    y = counts.values

    # Plot
    plt.figure(figsize=(6, 4))
    plt.scatter(x, y, color='#5b9bd5', s=80, alpha=0.5)

    # Pengaturan khusus untuk centrality
    if col in centrality_metrics:
        plt.xlim(-0.05, 1.05)
        plt.ylim(-10, y.max() + (y.max() * 0.1))
        plt.xlabel('Score', fontsize=11)
        filename = f'distribution_{col}_norm.png'
    else:
        plt.xlabel(col, fontsize=11)
        filename = f'distribution_{col}.png'

    # Judul dan styling
    plt.title(title_text, fontsize=14, pad=15)
    plt.ylabel('Count', fontsize=11)

    plt.grid(axis='y', linestyle='-', alpha=0.4)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)

    plt.tight_layout()

    # Simpan ke preprocesing/img
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()
    plt.close()