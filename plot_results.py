import csv
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

def generate_all_plots(csv_file: str = "experiment_results.csv"):
    data = defaultdict(lambda: defaultdict(list))
    
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                group = row.get("group", "").strip()
                
                # Table A: Time vs K
                if group == "A":
                    k_val = int(row["K"])
                    time_val = float(row["ch_assign_time"])
                    data["A"][k_val].append(time_val)
                    
                # Table B: Migration Rate vs N
                elif group == "B":
                    n_val = int(row["N"])
                    ch_rate = float(row["ch_add_rate"])
                    mod_rate = float(row["mod_add_rate"])
                    # หากค่าส่งมาเป็นเปอร์เซ็นต์ (0-100%) ปรับให้เป็นอัตราส่วน (0.0 - 1.0)
                    if ch_rate > 1.0:
                        ch_rate /= 100.0
                    if mod_rate > 1.0:
                        mod_rate /= 100.0
                    data["B"][n_val].append((ch_rate, mod_rate))
                    
                # Table C: Load Imbalance (CV) & Memory vs V
                elif group == "C":
                    v_val = int(row["V"])
                    cv_val = float(row["ch_cv"])
                    mem_val = float(row.get("ch_peak_mem", row.get("ch_curr_mem", 0.0)))
                    data["C"][v_val].append((cv_val, mem_val))

    except FileNotFoundError:
        print(f"❌ ไม่พบไฟล์ {csv_file}")
        return

    saved_charts = []

    # 📈 Chart A: Time vs K
    k_vals = sorted(data["A"].keys())
    if k_vals:
        times_mean = [np.mean(data["A"][k]) for k in k_vals]
        times_std = [np.std(data["A"][k]) for k in k_vals]

        plt.figure(figsize=(8, 5))
        plt.errorbar(k_vals, times_mean, yerr=times_std, fmt='-o', capsize=5, color='b', label='Consistent Hashing')
        plt.title('Execution Time vs. Number of Guests (K)')
        plt.xlabel('Number of Guests (K)')
        plt.ylabel('Time (seconds)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig('chart_a_time_vs_k.png')
        plt.close()
        saved_charts.append('chart_a_time_vs_k.png')

    # 📈 Chart B: Migration Rate vs N
    n_vals = sorted(data["B"].keys())
    if n_vals:
        ch_rates = [np.mean([x[0] for x in data["B"][n]]) for n in n_vals]
        mod_rates = [np.mean([x[1] for x in data["B"][n]]) for n in n_vals]

        plt.figure(figsize=(8, 5))
        plt.plot(n_vals, ch_rates, '-o', color='green', label='Consistent Hashing (1/N)')
        plt.plot(n_vals, mod_rates, '-s', color='red', label='Hash Mod N (~1.0)')
        plt.title('Migration Rate vs. Number of Buildings (N)')
        plt.xlabel('Number of Buildings (N)')
        plt.ylabel('Migration Rate')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig('chart_b_migration_vs_n.png')
        plt.close()
        saved_charts.append('chart_b_migration_vs_n.png')

    # 📈 Chart C: V vs CV & Memory
    v_vals = sorted(data["C"].keys())
    if v_vals:
        cv_means = [np.mean([x[0] for x in data["C"][v]]) for v in v_vals]
        mem_means = [np.mean([x[1] for x in data["C"][v]]) for v in v_vals]

        fig, ax1 = plt.subplots(figsize=(8, 5))

        ax1.set_xlabel('Virtual Nodes per Building (V)')
        ax1.set_ylabel('Coefficient of Variation (CV)', color='purple')
        ax1.plot(v_vals, cv_means, '-o', color='purple', label='Load Imbalance (CV)')
        ax1.tick_params(axis='y', labelcolor='purple')
        ax1.grid(True)

        ax2 = ax1.twinx()
        ax2.set_ylabel('Memory Usage (MiB)', color='orange')
        ax2.plot(v_vals, mem_means, '--s', color='orange', label='Peak Memory (MiB)')
        ax2.tick_params(axis='y', labelcolor='orange')

        plt.title('Load Imbalance (CV) and Memory Usage vs. Virtual Nodes (V)')
        fig.tight_layout()
        plt.savefig('chart_c_v_vs_cv_memory.png')
        plt.close()
        saved_charts.append('chart_c_v_vs_cv_memory.png')

    if saved_charts:
        print(f"📊 ทั้ง 3 กราฟสร้างสำเร็จเรียบร้อยแล้ว: {', '.join(saved_charts)}")

if __name__ == "__main__":
    generate_all_plots()