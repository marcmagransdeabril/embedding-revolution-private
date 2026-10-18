#!/usr/bin/env python3
import os
import re
import sys
import time
import json
import urllib.parse
import urllib.request
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import io

OUTPUT_DIR = "/home/marc/IM-LLM/references"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def clean_text(s):
    if not s:
        return ""
    # Remove bibtex braces
    s = re.sub(r'[{}]', '', s)
    # Remove common latex accents/escapes
    s = re.sub(r'\\[\'"`^~=](?:\{([a-zA-Z])\}|([a-zA-Z]))', r'\1\2', s)
    s = re.sub(r'\\([a-zA-Z]+)', r'', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def parse_bib_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    entries = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '@':
            brace_idx = text.find('{', i)
            paren_idx = text.find('(', i)
            if brace_idx == -1 and paren_idx == -1:
                break
            if brace_idx == -1: start_char, end_char, start_idx = '(', ')', paren_idx
            elif paren_idx == -1: start_char, end_char, start_idx = '{', '}', brace_idx
            else:
                if brace_idx < paren_idx: start_char, end_char, start_idx = '{', '}', brace_idx
                else: start_char, end_char, start_idx = '(', ')', paren_idx

            entry_type = text[i+1:start_idx].strip()
            
            depth = 1
            j = start_idx + 1
            while j < n and depth > 0:
                if text[j] == start_char:
                    depth += 1
                elif text[j] == end_char:
                    depth -= 1
                j += 1
            
            entry_body = text[start_idx+1:j-1]
            i = j
            
            first_comma = entry_body.find(',')
            if first_comma == -1:
                continue
            key = entry_body[:first_comma].strip()
            fields_str = entry_body[first_comma+1:]
            
            fields = {}
            k = 0
            fn = len(fields_str)
            while k < fn:
                eq_idx = fields_str.find('=', k)
                if eq_idx == -1:
                    break
                fname = fields_str[k:eq_idx].strip().lower()
                k = eq_idx + 1
                while k < fn and fields_str[k] in ' \t\r\n':
                    k += 1
                if k >= fn:
                    break
                
                val = ''
                if fields_str[k] == '{':
                    v_depth = 1
                    v_start = k + 1
                    k += 1
                    while k < fn and v_depth > 0:
                        if fields_str[k] == '{':
                            v_depth += 1
                        elif fields_str[k] == '}':
                            v_depth -= 1
                        k += 1
                    val = fields_str[v_start:k-1]
                elif fields_str[k] == '\"':
                    v_start = k + 1
                    k += 1
                    while k < fn and fields_str[k] != '\"':
                        if fields_str[k] == '\\\\':
                            k += 1
                        k += 1
                    val = fields_str[v_start:k]
                    k += 1
                else:
                    v_start = k
                    while k < fn and fields_str[k] not in ',\r\n':
                        k += 1
                    val = fields_str[v_start:k].strip()
                
                while k < fn and fields_str[k] in ',\r\n \t':
                    k += 1
                
                if fname:
                    fields[fname] = val.strip()
            
            entries.append({'type': entry_type, 'key': key, 'fields': fields})
        else:
            i += 1
    return entries

def is_valid_pdf_content(content):
    if not content or len(content) < 1000:
        return False
    if not (content.startswith(b'%PDF-') or b'%PDF-' in content[:1024]):
        return False
    try:
        reader = PdfReader(io.BytesIO(content))
        return len(reader.pages) > 0
    except Exception:
        # If PdfReader fails, check if %PDF- header exists and size > 10KB
        return content.startswith(b'%PDF-') and len(content) > 10000

def download_url(url, timeout=25, headers=None):
    if not headers:
        headers = HEADERS
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200 and is_valid_pdf_content(resp.content):
            return resp.content
    except Exception as e:
        pass
    return None

def try_arxiv(eprint):
    if not eprint:
        return None
    eprint = eprint.strip()
    # clean eprint
    eprint = re.sub(r'^(?:arxiv:)?', '', eprint, flags=re.I)
    urls = [
        f"https://arxiv.org/pdf/{eprint}.pdf",
        f"https://export.arxiv.org/pdf/{eprint}.pdf"
    ]
    for u in urls:
        content = download_url(u)
        if content:
            return content, u
    return None

def try_acl(doi):
    if not doi or not doi.startswith('10.18653/v1/'):
        return None
    anthology_id = doi.replace('10.18653/v1/', '').strip()
    url = f"https://aclanthology.org/{anthology_id}.pdf"
    content = download_url(url)
    if content:
        return content, url
    return None

def try_unpaywall(doi):
    if not doi:
        return None
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email=oa_miner@example.com"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            oa_loc = data.get('best_oa_location')
            if oa_loc:
                pdf_url = oa_loc.get('url_for_pdf') or oa_loc.get('url')
                if pdf_url:
                    content = download_url(pdf_url)
                    if content:
                        return content, pdf_url
            # try other oa locations
            for loc in data.get('oa_locations', []):
                pdf_url = loc.get('url_for_pdf') or loc.get('url')
                if pdf_url:
                    content = download_url(pdf_url)
                    if content:
                        return content, pdf_url
    except Exception:
        pass
    return None

def try_openalex(doi, title):
    # Try by DOI
    if doi:
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                for loc_key in ['best_oa_location', 'primary_location']:
                    loc = data.get(loc_key)
                    if loc and loc.get('pdf_url'):
                        content = download_url(loc['pdf_url'])
                        if content:
                            return content, loc['pdf_url']
                for loc in data.get('locations', []):
                    if loc.get('pdf_url'):
                        content = download_url(loc['pdf_url'])
                        if content:
                            return content, loc['pdf_url']
        except Exception:
            pass

    # Try by title search
    if title and len(title) > 10:
        clean_t = re.sub(r'[^\w\s]', ' ', title)
        url = f"https://api.openalex.org/works?filter=default.search:{urllib.parse.quote(clean_t)}&per_page=3"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                results = resp.json().get('results', [])
                for work in results:
                    for loc_key in ['best_oa_location', 'primary_location']:
                        loc = work.get(loc_key)
                        if loc and loc.get('pdf_url'):
                            content = download_url(loc['pdf_url'])
                            if content:
                                return content, loc['pdf_url']
                    for loc in work.get('locations', []):
                        if loc.get('pdf_url'):
                            content = download_url(loc['pdf_url'])
                            if content:
                                return content, loc['pdf_url']
        except Exception:
            pass
    return None

def try_scihub(doi):
    if not doi:
        return None
    mirrors = ['https://sci-hub.ru', 'https://sci-hub.st']
    for m in mirrors:
        try:
            url = f"{m}/{doi}"
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Look for iframe or embed or direct pdf link
                pdf_link = None
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    if href.endswith('.pdf') or '/storage/' in href:
                        pdf_link = href
                        break
                if not pdf_link:
                    for tag in soup.find_all(['embed', 'iframe']):
                        src = tag.get('src', '')
                        if src:
                            pdf_link = src
                            break
                if pdf_link:
                    if pdf_link.startswith('//'):
                        pdf_link = 'https:' + pdf_link
                    elif pdf_link.startswith('/'):
                        pdf_link = m + pdf_link
                    content = download_url(pdf_link)
                    if content:
                        return content, pdf_link
        except Exception:
            pass
    return None

def try_archive_org(title):
    if not title or len(title) < 5:
        return None
    clean_t = clean_text(title)
    # Search Internet Archive
    q = f'title:("{clean_t}") AND mediatype:(texts)'
    url = f"https://archive.org/advancedsearch.php?q={urllib.parse.quote(q)}&output=json&rows=5"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            docs = resp.json().get('response', {}).get('docs', [])
            for doc in docs:
                ident = doc.get('identifier')
                if not ident:
                    continue
                # Query metadata for files
                m_url = f"https://archive.org/metadata/{ident}/files"
                m_resp = requests.get(m_url, headers=HEADERS, timeout=10)
                if m_resp.status_code == 200:
                    files = m_resp.json().get('result', [])
                    for f in files:
                        fname = f.get('name', '')
                        if fname.lower().endswith('.pdf'):
                            pdf_url = f"https://archive.org/download/{ident}/{urllib.parse.quote(fname)}"
                            content = download_url(pdf_url, timeout=30)
                            if content:
                                return content, pdf_url
    except Exception:
        pass
    return None

def try_custom_sources(key, entry):
    fields = entry['fields']
    title = clean_text(fields.get('title', ''))
    doi = fields.get('doi', '')
    url = fields.get('url', '')

    # Known custom mappings
    CUSTOM_URLS = {
        'OECD2018': 'https://eacomm.com/support/innovation/oslomanual.pdf',
        'Kyffin2009': 'https://www.ijdesign.org/index.php/IJDesign/article/download/305/241',
        'Zahavy2026': 'https://icml.cc/virtual/2026/poster/67091', # might be web page or slides
        'Cursor2026': 'https://cursor.com/blog/agent-swarm-model-economics',
        'Brown2008': 'https://readings.design/PDF/Tim%20Brown%20Design%20Thinking.pdf',
        'Hauser1988': 'https://www.stat.purdue.edu/~wsk/stat598w/HouseOfQuality.pdf',
        'Schumpeter1934': 'https://archive.org/download/in.ernet.dli.2015.225302/2015.225302.The-Theory-Of-Economic-Development_text.pdf',
        'Boden2004': 'https://archive.org/download/margareta.bodenthecreativemindmythsandmechanismsroutledge2003/Margaret%20A.%20Boden%20-%20The%20Creative%20Mind_%20Myths%20and%20Mechanisms-Routledge%20%282003%29.pdf',
        'Brown2009': 'https://archive.org/download/ChangeByDesign/Change%20By%20Design.pdf',
    }

    if key in CUSTOM_URLS:
        target_url = CUSTOM_URLS[key]
        content = download_url(target_url, timeout=30)
        if content:
            return content, target_url

    # Check url field
    if url and url.endswith('.pdf'):
        content = download_url(url)
        if content:
            return content, url

    return None

def process_all_references():
    bib_path = "/home/marc/IM-LLM/paper/references.bib"
    entries = parse_bib_file(bib_path)
    print(f"Loaded {len(entries)} entries from {bib_path}")

    # Track unique keys
    seen_keys = set()
    unique_entries = []
    for e in entries:
        k = e['key']
        if k in seen_keys:
            # Handle duplicate key by appending suffix if fields differ
            suffix = 2
            while f"{k}_{suffix}" in seen_keys:
                suffix += 1
            e['key'] = f"{k}_{suffix}"
        seen_keys.add(e['key'])
        unique_entries.append(e)

    print(f"Processing {len(unique_entries)} unique keys...")

    results = {
        'downloaded': [],
        'failed': []
    }

    for idx, entry in enumerate(unique_entries, 1):
        key = entry['key']
        fields = entry['fields']
        title = clean_text(fields.get('title', ''))
        doi = fields.get('doi', '').strip()
        eprint = fields.get('eprint', '').strip()
        out_path = os.path.join(OUTPUT_DIR, f"{key}.pdf")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"[{idx}/{len(unique_entries)}] {key}: ALREADY EXISTS")
            results['downloaded'].append({'key': key, 'source': 'existing', 'path': out_path})
            continue

        print(f"[{idx}/{len(unique_entries)}] {key} - '{title[:50]}...'")
        pdf_data = None
        source_info = None

        # 1. Custom URL / Direct URL
        res = try_custom_sources(key, entry)
        if res:
            pdf_data, source_info = res
            print(f"  -> Found via Custom/Direct URL: {source_info}")

        # 2. arXiv
        if not pdf_data and eprint:
            res = try_arxiv(eprint)
            if res:
                pdf_data, source_info = res
                print(f"  -> Found via arXiv ({eprint})")

        # 3. ACL Anthology
        if not pdf_data and doi:
            res = try_acl(doi)
            if res:
                pdf_data, source_info = res
                print(f"  -> Found via ACL Anthology ({doi})")

        # 4. Unpaywall
        if not pdf_data and doi:
            res = try_unpaywall(doi)
            if res:
                pdf_data, source_info = res
                print(f"  -> Found via Unpaywall ({doi})")

        # 5. OpenAlex (DOI or Title)
        if not pdf_data:
            res = try_openalex(doi, title)
            if res:
                pdf_data, source_info = res
                print(f"  -> Found via OpenAlex")

        # 6. Sci-Hub (DOI)
        if not pdf_data and doi:
            res = try_scihub(doi)
            if res:
                pdf_data, source_info = res
                print(f"  -> Found via Sci-Hub ({doi})")

        # 7. Internet Archive
        if not pdf_data and title:
            res = try_archive_org(title)
            if res:
                pdf_data, source_info = res
                print(f"  -> Found via Internet Archive")

        if pdf_data:
            with open(out_path, 'wb') as f:
                f.write(pdf_data)
            size_kb = len(pdf_data) / 1024
            print(f"  SUCCESS: Saved {key}.pdf ({size_kb:.1f} KB)")
            results['downloaded'].append({'key': key, 'source': source_info, 'path': out_path, 'size_kb': size_kb})
        else:
            print(f"  FAILED: Could not find/download PDF for {key}")
            results['failed'].append({'key': key, 'doi': doi, 'eprint': eprint, 'title': title})

        # Small polite delay between requests
        time.sleep(0.2)

    print("\n" + "="*50)
    print(f"TOTAL DOWNLOADED: {len(results['downloaded'])} / {len(unique_entries)}")
    print(f"FAILED: {len(results['failed'])}")
    print("="*50)

    with open('/home/marc/IM-LLM/references/download_summary.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    process_all_references()
