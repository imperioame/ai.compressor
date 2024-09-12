# Simple File Compression Web Application
## Made by claude.ai
This simple web application does the following:

It provides a web interface where users can select multiple files to upload.
When files are uploaded, it compresses each file individually using a compression algorithm.
It creates a single file containing all compressed files, with metadata to distinguish between them.
It sends the compressed file back to the user for download.

### To use this:
- Install Flask if you haven't already: pip install Flask
- Run the application: python app.py
- Open a web browser and go to http://localhost:5000

Note that this is a basic implementation and lacks many features you'd want in a production system, such as error handling, security measures, and a more user-friendly interface. It also doesn't implement decompression - for that there's a separate script to decompress the files.

To decompress the files, the script decompressor.py reads the binary file, extracts each compressed file based on the metadata, and decompresses it. 

Remember, this is a basic implementation and should not be used for sensitive data without proper security measures. If you plan to use this in a production environment, you should add error handling, input validation, and security features.

## Live Demo
Although it's not fully developed, it can be used online in http://compressor.marioa.me/