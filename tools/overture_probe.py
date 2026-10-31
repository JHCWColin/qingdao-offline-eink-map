import duckdb, time
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
t=time.time()
q = """SELECT count(*) FROM read_parquet('s3://overturemaps-us-west-2/release/2026-10-21.0/theme=places/type=place/*', hive_partitioning=1)
WHERE bbox.xmin BETWEEN 120.30 AND 120.45 AND bbox.ymin BETWEEN 36.05 AND 36.12"""
print(con.execute(q).fetchall(), time.time()-t)
