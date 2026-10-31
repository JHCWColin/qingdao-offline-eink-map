#!/bin/bash
# Build data/out/qingdao.map from data/prepared.osm.pbf with the mapsforge writer.
cd "$(dirname "$0")/.."
O=tools/osmosis-0.49.2/lib
CP="$(ls $O/*.jar | tr '\n' ';')$O/default/mapsforge-map-writer-0.25.0-jar-with-dependencies.jar"
java -Xmx6g -cp "$CP" org.openstreetmap.osmosis.core.Osmosis \
  --read-pbf data/prepared.osm.pbf \
  --mapfile-writer file=data/out/qingdao.map type=ram bbox=35.40,119.45,37.20,121.62 \
  map-start-position=36.0662,120.3826 map-start-zoom=13 tag-conf-file=tools/tag-mapping.xml \
  label-position=true threads=4 comment="Qingdao offline e-ink map (c) OpenStreetMap contributors"
