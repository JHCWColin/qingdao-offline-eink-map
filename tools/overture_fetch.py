# Download Overture Maps places for the Qingdao bbox into a local parquet file.
import duckdb, time
REL = '2026-10-21.0'
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
t = time.time()
con.execute(f"""COPY (
  SELECT id, names, taxonomy, basic_category, confidence, addresses, phones, websites, brand, operating_status, sources,
         bbox.xmin AS lon, bbox.ymin AS lat
  FROM read_parquet('s3://overturemaps-us-west-2/release/{REL}/theme=places/type=place/*', hive_partitioning=1)
  WHERE bbox.xmin BETWEEN 119.45 AND 121.62 AND bbox.ymin BETWEEN 35.40 AND 37.20
) TO 'data/overture_places.parquet' (FORMAT PARQUET)""")
print('done', time.time() - t)
