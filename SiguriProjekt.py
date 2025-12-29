import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt

PRIMARY = "#0F9D58"
ACCENT = "#0B8043"
BG = "#FFFFFF"
CARD = "#FFFFFF"
TEXT = "#111111"


# ---------------- BACKEND ----------------

def fetch_transactions(address, timeout=10):
    """
    Fetch transactions from Blockchain API
    """
    url = f"https://blockchain.info/rawaddr/{address}"
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise Exception(f"Network error: {exc}") from exc

    if response.status_code != 200:
        raise Exception("Bitcoin address not found or API is not responding")

    data = response.json()
    return data.get("txs", [])


def parse_transactions(txs):
    """
    Parse transactions:
    returns list of records for use in table and graph.
    """
    records = []

    for tx in txs:
        tx_hash = tx.get("hash", "")
        timestamp = tx.get("time", 0)
        dt = datetime.fromtimestamp(timestamp)
        amount_btc = sum(out.get("value", 0) for out in tx.get("out", [])) / 1e8

        records.append({
            "hash_full": tx_hash or "",
            "hash": (tx_hash[:15] + "...") if tx_hash else "(no hash)",
            "dt": dt,
            "date_str": dt.strftime("%Y-%m-%d %H:%M"),
            "amount": round(amount_btc, 8)
        })

    return records


# ---------------- VISUALIZIM ----------------

def show_graph(records, group_by="Month", title_suffix=""):
    """
    Graph of transaction frequency over filtered data.
    - Day/Week/Month: line chart
    - Year: bar chart
    """
    if not records:
        return

    # Bucketing
    freq = {}
    if group_by == "Day":
        for r in records:
            k = r["dt"].date()
            freq[k] = freq.get(k, 0) + 1
        x_vals = sorted(freq.keys())
        y_vals = [freq[k] for k in x_vals]
        chart_type = "line"
        x_label = "Date"
    elif group_by == "Week":
        for r in records:
            dt = r["dt"]
            week_start = (dt - timedelta(days=dt.weekday())).date()
            freq[week_start] = freq.get(week_start, 0) + 1
        x_vals = sorted(freq.keys())
        y_vals = [freq[k] for k in x_vals]
        chart_type = "line"
        x_label = "Week (starts on Monday)"
    elif group_by == "Year":
        for r in records:
            k = r["dt"].year
            freq[k] = freq.get(k, 0) + 1
        x_vals = sorted(freq.keys())
        y_vals = [freq[k] for k in x_vals]
        chart_type = "bar"
        x_label = "Year"
    else:  # Month (default)
        for r in records:
            d = r["dt"]
            k = date(d.year, d.month, 1)
            freq[k] = freq.get(k, 0) + 1
        x_vals = sorted(freq.keys())
        y_vals = [freq[k] for k in x_vals]
        chart_type = "line"
        x_label = "Month"

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(10.5, 5.2), facecolor="#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    if chart_type == "bar":
        ax.bar(x_vals, y_vals, color="#2563EB")
    else:
        ax.plot(x_vals, y_vals, color="#2563EB", marker="o")

    ax.set_xlabel(x_label)
    ax.set_ylabel("Number of Transactions")
    title = f"Transactions by {x_label}"
    if title_suffix:
        title += f" — {title_suffix}"
    ax.set_title(title)

    ax.grid(True, axis="y", linestyle=":", alpha=0.6)
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()
    plt.show()


# ---------------- GUI LOGIC ----------------

def set_status(text, color="black"):
    status_label.config(text=text, foreground=color)


def handle_error(msg):
    set_status(msg, "red")
    btn.config(state="normal", text="Get Transactions")
    messagebox.showerror("Gabim", msg)


def update_table(records):
    # Clear the table
    for row in table.get_children():
        table.delete(row)

    # Fill the table
    for r in records:
        table.insert("", "end", values=(r["hash"], r["date_str"], r["amount"]))


def apply_filters():
    """Apply filters over all_records and update the table and graph."""
    if not all_records:
        return

    # Filter by period (friendly labels)
    sel = period_var.get()
    now = datetime.now()
    start_dt = None
    if sel == "Last 7 days":
        start_dt = now - timedelta(days=7)
    elif sel == "Last 30 days":
        start_dt = now - timedelta(days=30)
    elif sel == "Last 90 days":
        start_dt = now - timedelta(days=90)
    elif sel == "Last 1 year":
        start_dt = now - timedelta(days=365)
    elif sel == "Year to date":
        start_dt = datetime(now.year, 1, 1)
    # "All time" -> start_dt = None

    # Filter by transaction (hash contains)
    q = search_var.get().strip().lower()

    # Filter by amount
    min_txt = min_amount_var.get().strip()
    max_txt = max_amount_var.get().strip()
    try:
        min_val = float(min_txt) if min_txt else None
    except ValueError:
        messagebox.showwarning("Warning", "Min amount is not a valid number.")
        min_val = None
    try:
        max_val = float(max_txt) if max_txt else None
    except ValueError:
        messagebox.showwarning("Warning", "Max amount is not a valid number.")
        max_val = None

    filtered = []
    for r in all_records:
        if start_dt and r["dt"] < start_dt:
            continue
        if q and q not in (r["hash_full"].lower()):
            continue
        if (min_val is not None) and (r["amount"] < min_val):
            continue
        if (max_val is not None) and (r["amount"] > max_val):
            continue
        filtered.append(r)

    update_table(filtered)

    # Update the graph only if there is data
    if filtered:
        suffix = sel if sel and sel != "All time" else "All"
        group = group_by_var.get()
        show_graph(filtered, group_by=group, title_suffix=f"Period: {suffix}")
    else:
        messagebox.showinfo("Info", "No data after filtering.")


def update_after_fetch(records):
    global all_records
    all_records = records
    set_status("Ready", "green")
    btn.config(state="normal", text="Get Transactions")
    apply_filters()


def load_transactions(address):
    try:
        txs = fetch_transactions(address)
        records = parse_transactions(txs)
        root.after(0, lambda: update_after_fetch(records))
    except Exception as exc:
        root.after(0, lambda: handle_error(str(exc)))


def get_transactions():
    address = entry_address.get().strip()

    if not address:
        messagebox.showwarning("Error", "Please enter a Bitcoin address!")
        return

    set_status("Fetching data...", "blue")
    btn.config(state="disabled", text="Working...")

    worker = threading.Thread(target=load_transactions, args=(address,), daemon=True)
    worker.start()


# ---------------- GUI ----------------

root = tk.Tk()
root.title("Bitcoin Transaction Analyzer")
root.geometry("920x620")
root.minsize(820, 560)
root.configure(bg=BG)

# Center window on screen
root.update_idletasks()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
size = tuple(int(x) for x in root.geometry().split('+')[0].split('x'))
x = screen_w//2 - size[0]//2
y = screen_h//2 - size[1]//2
root.geometry(f"{size[0]}x{size[1]}+{x}+{y}")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background=BG, foreground=TEXT)
style.configure("TFrame", background=BG)
style.configure(
    "Treeview",
    background="#FFFFFF",
    fieldbackground="#FFFFFF",
    foreground="#111111",
    rowheight=26,
    bordercolor="#DDDDDD",
    borderwidth=1,
    font=("Segoe UI", 10)
)
style.configure(
    "Treeview.Heading",
    background="#F3F4F6",
    foreground="#111111",
    font=("Segoe UI Semibold", 10)
)
style.map("Treeview", background=[("selected", "#E6F4EA")])

header = ttk.Frame(root, padding=(16, 14, 16, 10))
header.pack(fill="x")

title = ttk.Label(header, text="Bitcoin Transaction Analyzer",
                  font=("Segoe UI Semibold", 20))
title.pack(anchor="center")

subtitle = ttk.Label(header, text="Enter address, select period and filter by hash/amount",
                     font=("Segoe UI", 10))
subtitle.pack(anchor="center", pady=(4, 0))

form = ttk.Frame(root, padding=(16, 0, 16, 6))
form.pack(fill="x")

entry_address = tk.Entry(form, width=70, bg="#FFFFFF", fg="#111111", insertbackground="#111111",
                        relief="solid", bd=1, font=("Segoe UI", 11))
entry_address.pack(pady=6, padx=10, ipady=6, fill="x", expand=True)
entry_address.insert(0, "1BoatSLRHtKNngkdXEeobR76b53LETtpyT")

btn = tk.Button(
    form,
    text="Get Transactions",
    command=get_transactions,
    bg=PRIMARY,
    activebackground=ACCENT,
    fg="white",
    relief="flat",
    padx=16,
    pady=10,
    font=("Segoe UI Semibold", 10)
)
btn.pack()

# Filter panel
filters = ttk.Frame(root, padding=(16, 0, 16, 8))
filters.pack(fill="x")

period_var = tk.StringVar(value="Last 1 year")
group_by_var = tk.StringVar(value="Month")
search_var = tk.StringVar()
min_amount_var = tk.StringVar()
max_amount_var = tk.StringVar()

row1 = ttk.Frame(filters)
row1.pack(fill="x", pady=4)

ttk.Label(row1, text="Period:", font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
period_combo = ttk.Combobox(row1, textvariable=period_var, width=18, state="readonly",
                            values=[
                                "All time",
                                "Last 7 days",
                                "Last 30 days",
                                "Last 90 days",
                                "Year to date",
                                "Last 1 year",
                            ])
period_combo.pack(side="left", padx=(0, 16))

ttk.Label(row1, text="Group by:", font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
group_combo = ttk.Combobox(row1, textvariable=group_by_var, width=10, state="readonly",
                           values=["Day", "Week", "Month", "Year"])
group_combo.pack(side="left", padx=(0, 16))

ttk.Label(row1, text="Transaction contains:", font=("Segoe UI", 10)).pack(side="left", padx=(10, 6))
search_entry = ttk.Entry(row1, textvariable=search_var, width=28)
search_entry.pack(side="left", padx=(0, 10))

ttk.Label(row1, text="Min amount:", font=("Segoe UI", 10)).pack(side="left", padx=(10, 6))
min_entry = ttk.Entry(row1, textvariable=min_amount_var, width=12)
min_entry.pack(side="left", padx=(0, 10))

ttk.Label(row1, text="Max amount:", font=("Segoe UI", 10)).pack(side="left", padx=(10, 6))
max_entry = ttk.Entry(row1, textvariable=max_amount_var, width=12)
max_entry.pack(side="left", padx=(0, 10))

apply_btn = tk.Button(row1, text="Apply Filters", command=apply_filters,
                      bg="#2563EB", fg="white", activebackground="#1D4ED8",
                      relief="flat", padx=12, pady=6, font=("Segoe UI Semibold", 10))
apply_btn.pack(side="left", padx=(10, 0))

status_label = ttk.Label(root, text="Ready", foreground="#0B8043", font=("Segoe UI", 9))
status_label.pack(anchor="center", padx=18, pady=(0, 8))

table_frame = ttk.Frame(root, padding=(14, 0, 14, 14))
table_frame.pack(fill="both", expand=True)

columns = ("hash", "date", "amount")
table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

table.heading("hash", text="Transaction Hash")
table.heading("date", text="Date/Time")
table.heading("amount", text="Amount (BTC)")

table.column("hash", width=360, anchor="w")
table.column("date", width=200, anchor="center")
table.column("amount", width=160, anchor="e")

vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
table.configure(yscrollcommand=vsb.set)

table.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
table_frame.columnconfigure(0, weight=1)
table_frame.rowconfigure(0, weight=1)

# Enter in search/amount -> apply filters
search_entry.bind("<Return>", lambda e: apply_filters())
min_entry.bind("<Return>", lambda e: apply_filters())
max_entry.bind("<Return>", lambda e: apply_filters())
period_combo.bind("<<ComboboxSelected>>", lambda e: apply_filters())
group_combo.bind("<<ComboboxSelected>>", lambda e: apply_filters())

all_records = []

root.mainloop()

# TO RUN THE SCRIPT USE THE FOLLOWING COMMAND IN TERMINAL:
# & ".venv/Scripts/python.exe" "SiguriProjekt.py"