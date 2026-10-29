import sys, pyarrow.ipc as ipc, pyarrow as pa
for p in sys.argv[1:]:
    r = ipc.open_file(p)
    print("##", p.split("/")[-1], "rows:", sum(r.get_batch(i).num_rows for i in range(r.num_record_batches)) if r.num_record_batches < 5000 else "?", "batches:", r.num_record_batches)
    print(r.schema)
    print("meta:", r.schema.metadata and {k[:40]: v[:300] for k, v in r.schema.metadata.items()})
