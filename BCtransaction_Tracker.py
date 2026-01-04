import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import csv

# ---------------- STYLES ----------------
PRIMARY = "#0F9D58"
ACCENT = "#0B8043"
BG = "#F4F4F9"
CARD = "#FFFFFF"
TEXT = "#111111"
BTN_COLOR = "#2563EB"
BTN_HOVER = "#1D4ED8"

# ---------------- BACKEND ----------------

def fetch_transactions(address, timeout=10):
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
    records = []
    for tx in txs:
        tx_hash = tx.get("hash", "")
        timestamp = tx.get("time", 0)
        dt = datetime.fromtimestamp(timestamp)
        result_sats = tx.get("result", 0) or 0
        amount_btc = abs(result_sats) / 1e8
        records.append({
            "hash_full": tx_hash or "",
            "hash": (tx_hash[:15] + "...") if tx_hash else "(no hash)",
            "dt": dt,
            "date_str": dt.strftime("%Y-%m-%d %H:%M"),
            "amount": round(amount_btc, 8)
        })
    return records

# ---------------- GRAFIKET ----------------

def plot_transaction_frequency(records, group_by="Month"):
    if not records: return messagebox.showwarning("Warning","Nuk ka të dhëna.")
    first_year = min(r["dt"].year for r in records)
    last_year = max(r["dt"].year for r in records)
    freq = {date(y,m,1):0 for y in range(first_year,last_year+1) for m in range(1,13)}
    for r in records:
        freq[date(r["dt"].year,r["dt"].month,1)] += 1
    x_vals = sorted(freq.keys())
    y_vals = [freq[k] for k in x_vals]
    plt.figure(figsize=(10,5))
    plt.plot(x_vals,y_vals,marker="o",color="#2563EB", linewidth=2)
    plt.title("Transaction Frequency per Month", fontsize=14, fontweight="bold")
    plt.xlabel("Month"); plt.ylabel("Transactions")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.show()

def plot_transaction_volume(records, group_by="Month"):
    if not records: return messagebox.showwarning("Warning","Nuk ka të dhëna.")
    first_year = min(r["dt"].year for r in records)
    last_year = max(r["dt"].year for r in records)
    volume = {date(y,m,1):0 for y in range(first_year,last_year+1) for m in range(1,13)}
    for r in records:
        volume[date(r["dt"].year,r["dt"].month,1)] += r["amount"]
    x_vals = sorted(volume.keys())
    y_vals = [volume[k] for k in x_vals]
    plt.figure(figsize=(10,5))
    plt.plot(x_vals,y_vals,marker="o",color="#16A34A", linewidth=2)
    plt.title("Transaction Volume (BTC) per Month", fontsize=14, fontweight="bold")
    plt.xlabel("Month"); plt.ylabel("BTC Volume")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.show()

def plot_amount_distribution(records):
    if not records: return
    amounts = [r["amount"] for r in records if r["amount"] > 0]
    plt.figure(figsize=(8,5))
    plt.hist(amounts,bins=30,color="#7C3AED", edgecolor="#4C1D95")
    plt.title("Distribution of Transaction Amounts (BTC)", fontsize=14,fontweight="bold")
    plt.xlabel("Amount (BTC)"); plt.ylabel("Frequency")
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    plt.show()

def plot_weekday_activity(records):
    if not records: return
    weekdays = {i:0 for i in range(7)}
    for r in records: weekdays[r["dt"].weekday()] += 1
    labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    values = [weekdays[i] for i in range(7)]
    plt.figure(figsize=(8,5))
    plt.bar(labels,values,color="#F59E0B",edgecolor="#B45309")
    plt.title("Transaction Activity by Weekday", fontsize=14,fontweight="bold")
    plt.xlabel("Day"); plt.ylabel("Transactions")
    plt.grid(True, axis="y", linestyle=":", alpha=0.5)
    plt.tight_layout()
    plt.show()

# ---------------- GUI ----------------

def set_status(text,color="black"): status_label.config(text=text, foreground=color)
def handle_error(msg): set_status(msg,"red"); btn.config(state="normal",text="Get Transactions"); messagebox.showerror("Error",msg)
def update_table(records):
    for row in table.get_children(): table.delete(row)
    for r in records: table.insert("", "end", values=(r["hash"], r["date_str"], r["amount"]))

def export_to_csv():
    if not table.get_children(): return messagebox.showwarning("Warning","Nuk ka të dhëna për eksportim.")
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")], title="Ruaj CSV")
    if not file_path: return
    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f); writer.writerow(["Transaction Hash","Date/Time","Amount (BTC)"])
            for row_id in table.get_children(): writer.writerow(table.item(row_id)["values"])
        messagebox.showinfo("Sukses","Të dhënat u ruajtën me sukses!")
    except Exception as e: messagebox.showerror("Gabim", f"Gabim gjatë ruajtjes: {e}")

def apply_filters():
    if not all_records: return []
    sel = period_var.get(); now = datetime.now(); start_dt=None
    if sel=="Last 7 days": start_dt=now-timedelta(days=7)
    elif sel=="Last 30 days": start_dt=now-timedelta(days=30)
    elif sel=="Last 90 days": start_dt=now-timedelta(days=90)
    elif sel=="Last 1 year": start_dt=now-timedelta(days=365)
    elif sel=="Year to date": start_dt=datetime(now.year,1,1)
    q = search_var.get().strip().lower()
    min_val = float(min_amount_var.get()) if min_amount_var.get().strip() else None
    max_val = float(max_amount_var.get()) if max_amount_var.get().strip() else None
    filtered=[]
    for r in all_records:
        if start_dt and r["dt"]<start_dt: continue
        if q and q not in r["hash_full"].lower(): continue
        if min_val is not None and r["amount"]<min_val: continue
        if max_val is not None and r["amount"]>max_val: continue
        filtered.append(r)
    update_table(filtered); update_security_insights(filtered); return filtered

def update_after_fetch(records):
    global all_records; all_records = records
    set_status("Ready","green"); btn.config(state="normal",text="Get Transactions")
    apply_filters()

def load_transactions(address):
    try:
        txs = fetch_transactions(address)
        records = parse_transactions(txs)
        root.after(0, lambda:update_after_fetch(records))
    except Exception as exc: root.after(0, lambda:handle_error(str(exc)))

def get_transactions():
    address = entry_address.get().strip()
    if not address: messagebox.showwarning("Error","Please enter a Bitcoin address!"); return
    set_status("Fetching data...","blue"); btn.config(state="disabled",text="Working...")
    threading.Thread(target=load_transactions,args=(address,),daemon=True).start()

def update_security_insights(records):
    if not records: insights_text.set("Nuk ka të dhëna për analizë sigurie."); return
    dates=[r["dt"] for r in records]; start=min(dates).strftime("%Y-%m-%d"); end=max(dates).strftime("%Y-%m-%d")
    count=len(records)
    insights_text.set(f"Total Transactions: {count}\nActivity Period: {start} → {end}\n\nSecurity Insight:\nAlthough Bitcoin addresses do not contain personal identity,\ntransaction patterns such as timing and frequency can be analyzed.\nThis reduces anonymity and enables transaction traceability.")

# ---------------- GUI ----------------
root=tk.Tk()
root.title("Bitcoin Transaction Analyzer")
root.geometry("1050x660"); root.configure(bg=BG)

# Header
header=tk.Frame(root,bg=BG); header.pack(fill="x",padx=16,pady=10)
tk.Label(header,text="Bitcoin Transaction Analyzer",font=("Segoe UI Semibold",22),bg=BG).pack()
tk.Label(header,text="Enter address, filter period, min/max, hash",font=("Segoe UI",11),bg=BG).pack()

# Address & Fetch
form=tk.Frame(root,bg=BG); form.pack(fill="x",padx=16,pady=6)
entry_address=tk.Entry(form,bg=CARD,fg=TEXT,insertbackground=TEXT,relief="solid",bd=1,font=("Segoe UI",11))
entry_address.pack(fill="x",ipady=6); entry_address.insert(0,"1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
btn=tk.Button(form,text="Get Transactions",command=get_transactions,bg=PRIMARY,fg="white",activebackground=ACCENT,relief="flat",font=("Segoe UI Semibold",11))
btn.pack(pady=6)

# Filters
filters=tk.LabelFrame(root,text="Filters",bg=BG,fg=TEXT,font=("Segoe UI Semibold",10))
filters.pack(fill="x",padx=16,pady=8)
period_var=tk.StringVar(value="Last 1 year"); search_var=tk.StringVar(); min_amount_var=tk.StringVar(); max_amount_var=tk.StringVar()
ttk.Label(filters,text="Period:").pack(side="left",padx=(8,2))
ttk.Combobox(filters,textvariable=period_var,state="readonly",values=["All time","Last 7 days","Last 30 days","Last 90 days","Year to date","Last 1 year"],width=12).pack(side="left",padx=(0,10))
ttk.Label(filters,text="Transaction contains:").pack(side="left",padx=(2,2))
ttk.Entry(filters,textvariable=search_var,width=18).pack(side="left",padx=(0,10))
ttk.Label(filters,text="Min:").pack(side="left",padx=(2,2)); ttk.Entry(filters,textvariable=min_amount_var,width=8).pack(side="left",padx=(0,10))
ttk.Label(filters,text="Max:").pack(side="left",padx=(2,2)); ttk.Entry(filters,textvariable=max_amount_var,width=8).pack(side="left",padx=(0,10))
ttk.Button(filters,text="Apply Filters",command=apply_filters).pack(side="left",padx=(10,5))
ttk.Button(filters,text="Export CSV",command=export_to_csv).pack(side="left",padx=(5,5))

# Grafik Buttons
gfx_frame=tk.LabelFrame(root,text="Graphs",bg=BG,fg=TEXT,font=("Segoe UI Semibold",10))
gfx_frame.pack(fill="x",padx=16,pady=6)
tk.Button(gfx_frame,text="Frequency per Month",bg=BTN_COLOR,fg="white",command=lambda:plot_transaction_frequency(apply_filters()),relief="flat",padx=8,pady=4).pack(side="left",padx=5)
tk.Button(gfx_frame,text="Volume per Month",bg="#16A34A",fg="white",command=lambda:plot_transaction_volume(apply_filters()),relief="flat",padx=8,pady=4).pack(side="left",padx=5)
tk.Button(gfx_frame,text="Amount Distribution",bg="#7C3AED",fg="white",command=lambda:plot_amount_distribution(apply_filters()),relief="flat",padx=8,pady=4).pack(side="left",padx=5)
tk.Button(gfx_frame,text="Weekday Activity",bg="#F59E0B",fg="white",command=lambda:plot_weekday_activity(apply_filters()),relief="flat",padx=8,pady=4).pack(side="left",padx=5)

# Table
table_frame=tk.Frame(root,bg=BG); table_frame.pack(fill="both",expand=True,padx=16,pady=6)
columns=("hash","date","amount"); table=ttk.Treeview(table_frame,columns=columns,show="headings")
for c in columns: table.heading(c,text=c.title()); table.column(c,width=200 if c!="hash" else 380)
vsb=ttk.Scrollbar(table_frame,orient="vertical",command=table.yview); table.configure(yscrollcommand=vsb.set)
table.grid(row=0,column=0,sticky="nsew"); vsb.grid(row=0,column=1,sticky="ns")
table_frame.columnconfigure(0,weight=1); table_frame.rowconfigure(0,weight=1)

# Security Insights
insights_text=tk.StringVar()
insights_label=tk.Label(root,textvariable=insights_text,bg=BG,justify="left",wraplength=1000,font=("Segoe UI",10))
insights_label.pack(fill="x",padx=16,pady=(0,10))
insights_text.set("Ngarko transaksionet për të parë analizën e sigurisë.")

# Status
status_label=tk.Label(root,text="Ready",foreground=ACCENT,bg=BG,font=("Segoe UI",9))
status_label.pack(anchor="center",pady=(0,8))

all_records=[]

root.mainloop()