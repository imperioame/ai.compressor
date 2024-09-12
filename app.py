from flask import Flask, request, send_file, render_template, jsonify, redirect, url_for, send_from_directory
import zlib
import zstandard as zstd
import io
import os
import base64
import csv
import json
import re
import tempfile
import shutil
import zipfile

app = Flask(__name__)

MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB
ZSTD_COMPRESSION_LEVEL = 22  # Highest zstandard compression level

def is_text_file(content, file_name):
    text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.csv'}
    if any(file_name.lower().endswith(ext) for ext in text_extensions):
        return True
    try:
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def preprocess_text(content):
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='ignore')
    content = re.sub(r'(?m)^\s*#.*\n?', '', content)
    content = re.sub(r'(?m)^\s*//.*\n?', '', content)
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'^\s+|\s+$', '', content, flags=re.MULTILINE)
    return content.encode('utf-8')

def compress_and_encode_standard(content):
    return base64.b64encode(zlib.compress(content)).decode('utf-8')

def compress_and_encode_high(content, file_name):
    if is_text_file(content, file_name):
        content = preprocess_text(content)
    cctx = zstd.ZstdCompressor(level=ZSTD_COMPRESSION_LEVEL)
    compressed = cctx.compress(content)
    return base64.b64encode(compressed).decode('utf-8')

def split_content(content, max_size):
    return [content[i:i+max_size] for i in range(0, len(content), max_size)]

@app.route('/', methods=['GET', 'POST'])
def compress_project():
    if request.method == 'POST':
        files = request.files.getlist('files')
        output_format = request.form.get('format', 'json')
        compression_method = request.form.get('compression', 'high')
        
        if not files:
            return "No files uploaded", 400

        compressed_files = []
        total_original_size = 0
        total_compressed_size = 0
        file_structure = []
        for file in files:
            relative_path = file.filename
            file_structure.append(relative_path)
            content = file.read()
            total_original_size += len(content)
            if compression_method == 'standard':
                compressed = compress_and_encode_standard(content)
            else:
                compressed = compress_and_encode_high(content, relative_path)
            total_compressed_size += len(compressed)
            compressed_files.append((relative_path, compressed))

        if output_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['path', 'compressed_content'])
            writer.writerows(compressed_files)
            content = output.getvalue()
        elif output_format == 'txt':
            content = '\n'.join([f"{path}:{compressed}" for path, compressed in compressed_files])
        else:  # JSON
            content = json.dumps(dict(compressed_files))

        compression_ratio = (total_original_size / total_compressed_size) if total_compressed_size > 0 else 0
        
        # Create a temporary file to store the compressed content
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=f'.{output_format}') as temp_file:
            temp_file.write(content)
        
        return jsonify({
            'message': 'Compression successful',
            'file_path': temp_file.name,
            'compression_method': compression_method,
            'file_structure': file_structure
        })

    return render_template('compress.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

def decompress_content(compressed, method):
    decoded = base64.b64decode(compressed)
    if method == 'standard':
        return zlib.decompress(decoded)
    else:  # high compression
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(decoded)

@app.route('/decompress', methods=['GET', 'POST'])
def decompress_project():
    if request.method == 'POST':
        compressed_file = request.files['compressed_file']
        compression_method = request.form.get('compression', 'high')
        
        if not compressed_file:
            return "No file uploaded", 400

        # Create a temporary directory to store decompressed files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_content = compressed_file.read().decode('utf-8')
            
            try:
                data = json.loads(file_content)
            except json.JSONDecodeError:
                try:
                    reader = csv.reader(io.StringIO(file_content))
                    data = dict(reader)
                except:
                    data = dict(line.strip().split(':', 1) for line in file_content.splitlines())

            for path, compressed in data.items():
                content = decompress_content(compressed, compression_method)
                full_path = os.path.join(temp_dir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'wb') as out_file:
                    out_file.write(content)

            # Create a zip file of the decompressed contents
            zip_path = os.path.join(temp_dir, 'decompressed_project.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)

            return send_file(zip_path, as_attachment=True, download_name='decompressed_project.zip')

    return render_template('decompress.html')

if __name__ == '__main__':
    app.run(debug=True)