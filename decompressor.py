import zlib
import zstandard as zstd
import base64
import json
import csv
import os

def decompress_content(compressed, method):
    decoded = base64.b64decode(compressed)
    if method == 'standard':
        return zlib.decompress(decoded)
    else:  # high compression
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(decoded)

def decompress_project(filename):
    _, ext = os.path.splitext(filename)
    format = ext[1:]  # Remove the dot
    
    # Determine compression method from filename
    if 'standard' in filename:
        method = 'standard'
    else:
        method = 'high'

    with open(filename, 'r') as f:
        if format == 'json':
            data = json.load(f)
        elif format == 'csv':
            reader = csv.reader(f)
            next(reader)  # Skip header
            data = dict(reader)
        else:  # txt
            data = dict(line.strip().split(':', 1) for line in f)

    for path, compressed in data.items():
        content = decompress_content(compressed, method)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as out_file:
            out_file.write(content)
        print(f"Decompressed: {path}")

# Usage
decompress_project('compressed_project_standard.json')  # or high, .csv, .txt