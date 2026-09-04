from flask import Flask, render_template, jsonify, send_file
import os
import json
import pandas as pd
import shapefile
import simplekml
import zipfile
import io

app = Flask(__name__, static_folder="static", template_folder="templates")
OUTPUT_DIR = "../output/chorabari"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def get_data():
    comparison_path = os.path.join(OUTPUT_DIR, "comparison_report.json")
    damage_path = os.path.join(OUTPUT_DIR, "damage.csv")
    
    comparison = {}
    if os.path.exists(comparison_path):
        with open(comparison_path, "r") as f:
            comparison = json.load(f)
            
    damage = []
    if os.path.exists(damage_path):
        df = pd.read_csv(damage_path)
        damage = df.to_dict(orient="records")
        
    return jsonify({"comparison": comparison, "damage": damage})

@app.route("/api/export/<format>")
def export_data(format):
    damage_path = os.path.join(OUTPUT_DIR, "damage.csv")
    if not os.path.exists(damage_path):
        return "No data to export", 404
        
    df = pd.read_csv(damage_path)
    if 'lon' not in df.columns or 'lat' not in df.columns:
        return "Invalid damage CSV format", 400
        
    os.makedirs("exports", exist_ok=True)
    
    if format == "shp":
        w = shapefile.Writer("exports/damage")
        w.field("building_id", "C")
        w.field("depth_m", "F", 10, 2)
        w.field("arrival_s", "N")
        w.field("damage", "C")
        
        for _, row in df.iterrows():
            w.point(row['lon'], row['lat'])
            depth = row.get('max_depth_m', 0)
            arrival = row.get('arrival_time_s', 0)
            dclass = row.get('damage_class', 'unknown')
            w.record(str(row.get('building_id', '')), depth, arrival, dclass)
        w.close()
        
        # Create PRJ file for EPSG:4326
        with open("exports/damage.prj", "w") as f:
            f.write('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')
            
        # Zip them up
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                zf.write(f"exports/damage{ext}", f"damage{ext}")
        memory_file.seek(0)
        return send_file(memory_file, download_name="damage.zip", as_attachment=True)
        
    elif format == "kml":
        kml = simplekml.Kml()
        for _, row in df.iterrows():
            depth = row.get('max_depth_m', 0)
            pnt = kml.newpoint(name=str(row.get('building_id', '')), coords=[(row['lon'], row['lat'])])
            pnt.description = f"Depth: {depth}m, Arrival: {row.get('arrival_time_s', 0)}s, Class: {row.get('damage_class', 'unknown')}"
        kml.save("exports/damage.kml")
        return send_file("exports/damage.kml", as_attachment=True)
    else:
        return "Unsupported format", 400

if __name__ == "__main__":
    app.run(debug=True, port=8080)
