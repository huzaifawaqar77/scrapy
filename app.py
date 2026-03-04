from flask import Flask, jsonify, render_template, Response, stream_with_context
from job_scraper.db import Session, JobPost
import os
import subprocess
import sys
import json
import threading

app = Flask(__name__)

# Security: Global execution lock to prevent Denial of Service (DoS) by spamming the scraper
SCRAPE_LOCK = threading.Lock()

# Security Headers to prevent basic XSS and Clickjacking
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Adding a basic Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net;"
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pipeline')
def pipeline():
    return render_template('pipeline.html')

@app.route('/api/scrape/stream')
def scrape_stream():
    """Stream real-time output of the Scrapy process via Server-Sent Events (SSE)."""
    
    # Check if a scrape is already running to prevent DoS attacks
    if not SCRAPE_LOCK.acquire(blocking=False):
        def busy_response():
            yield "data: {\"type\": \"warning\", \"msg\": \"[SECURITY] A pipeline execution is already in progress. Please wait.\"}\n\n"
            yield "event: end\ndata: {}\n\n"
        return Response(stream_with_context(busy_response()), mimetype='text/event-stream')

    def generate():
        try:
            # Use python -m scrapy to ensure it runs within the virtual environment Python
            scraper_dir = os.path.join(os.path.dirname(__file__), 'job_scraper')
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"  # Force unbuffered output for real-time streaming

            cmd = [sys.executable, "-m", "scrapy", "runspider", "spiders/python_jobs.py", "-L", "INFO"]
            
            process = subprocess.Popen(
                cmd,
                cwd=scraper_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1 # Line buffered
            )

            yield "data: {\"type\": \"system\", \"msg\": \"[SYSTEM] Initiating Secure Data Pipeline...\"}\n\n"
            yield "data: {\"type\": \"system\", \"msg\": \"[SYSTEM] Spinning up Spider: python_jobs\"}\n\n"

            for line in iter(process.stdout.readline, ''):
                if line:
                    clean_line = line.strip()
                    # Yield JSON packed log lines to the frontend
                    yield f"data: {json.dumps({'type': 'log', 'msg': clean_line})}\n\n"

            process.stdout.close()
            process.wait()
            
            yield f"data: {json.dumps({'type': 'system', 'msg': f'[SYSTEM] Pipeline execution terminated with code {process.returncode}'})}\n\n"
            
        finally:
            # Always ensure the lock is released when the interaction closes or crashes
            SCRAPE_LOCK.release()
            yield "event: end\ndata: {}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/jobs')
def get_jobs():
    try:
        session = Session()
        # Fetch the latest 100 jobs
        jobs = session.query(JobPost).order_by(JobPost.scraped_at.desc()).limit(100).all()
        
        jobs_data = [{
            'id': j.id,
            'title': j.title,
            'company': j.company,
            'location': j.location if j.location else 'Remote',
            'salary': j.salary if j.salary else 'Not specified',
            'job_url': j.job_url,
            'source_board': j.source_board,
            'scraped_at': j.scraped_at.strftime('%b %d, %Y') if j.scraped_at else 'Recently'
        } for j in jobs]
        
        session.close()
        return jsonify({"status": "success", "data": jobs_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run locally 
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=True)