# Run this in Google Colab (or any machine with internet). It downloads Bitcoin blocks for the FRESH confirmation period
# (2021-04-01 .. 2021-10-01) from the same public APIs used by the notebook, and writes ONE file: fresh_blocks.parquet
# Then upload fresh_blocks.parquet to the chat.  No account / key needed.  Resumable (re-run if it stops).
import time, pickle, os, requests, pandas as pd, concurrent.futures as cf
API = ["https://mempool.space/api", "https://blockstream.info/api"]
H_LO, H_HI = 677_000, 706_000          # 677,000 gives the feature warm-up; 706,000 is past 2021-10-01
CK = "fresh_checkpoint.pkl"
done = pickle.load(open(CK, "rb")) if os.path.exists(CK) else {}
todo = [h for h in range(H_HI, H_LO, -10) if h not in done]
print(len(todo), "pages to fetch")
s = requests.Session(); s.headers.update({"User-Agent": "research-notebook/1.0"})
def one(h):
    for a in range(8):
        try:
            r = s.get(f"{API[(a // 2) % 2]}/blocks/{h}", timeout=30)
            if r.status_code == 200:
                return h, [(b["height"], b["timestamp"], b["tx_count"], b["size"], b["weight"]) for b in r.json()]
        except Exception:
            pass
        time.sleep(min(30, 2 ** a))
    return h, None
fail = 0
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for i, (h, rows) in enumerate(ex.map(one, todo), 1):
        if rows is None: fail += 1
        else: done[h] = rows
        if i % 100 == 0: pickle.dump(done, open(CK, "wb")); print(i, "/", len(todo))
pickle.dump(done, open(CK, "wb"))
assert not fail, f"{fail} pages failed: just run this cell again (it resumes)"
r = pd.DataFrame([x for v in done.values() for x in v], columns=["number", "ts", "transaction_count", "size", "weight"]).drop_duplicates("number")
r["block_timestamp"] = pd.to_datetime(r["ts"], unit="s", utc=True)
r = r[(r.block_timestamp >= "2021-03-25") & (r.block_timestamp < "2021-10-01")].sort_values("number").reset_index(drop=True)
assert (r.number.diff().dropna() == 1).all(), "gaps in block numbers"
r[["number", "block_timestamp", "transaction_count", "size", "weight"]].to_parquet("fresh_blocks.parquet")
print(len(r), "blocks", r.block_timestamp.min(), "->", r.block_timestamp.max())
try:
    from google.colab import files; files.download("fresh_blocks.parquet")
except Exception: pass
