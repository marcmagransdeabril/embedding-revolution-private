#!/usr/bin/env python3
import os
import re
import json
import io
import subprocess
from pypdf import PdfReader

BIB_PATH = "/home/marc/IM-LLM/paper/references.bib"
PDF_DIR = "/home/marc/IM-LLM/references"

STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'can\'t', 'cannot',
    'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t', 'down', 'during', 'each',
    'few', 'for', 'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d',
    'he\'ll', 'he\'s', 'her', 'here', 'here\'s', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'how\'s', 'i',
    'i\'d', 'i\'ll', 'i\'m', 'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s',
    'me', 'more', 'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or',
    'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan\'t', 'she', 'she\'d', 'she\'ll',
    'she\'s', 'should', 'shouldn\'t', 'so', 'some', 'such', 'than', 'that', 'that\'s', 'the', 'their', 'theirs',
    'them', 'themselves', 'then', 'there', 'there\'s', 'these', 'they', 'they\'d', 'they\'ll', 'they\'re', 'they\'ve',
    'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll',
    'we\'re', 'we\'ve', 'were', 'weren\'t', 'what', 'what\'s', 'when', 'when\'s', 'where', 'where\'s', 'which', 'while',
    'who', 'who\'s', 'whom', 'why', 'why\'s', 'with', 'won\'t', 'would', 'wouldn\'t', 'you', 'you\'d', 'you\'ll',
    'you\'re', 'you\'ve', 'your', 'yours', 'yourself', 'yourselves', 'towards', 'toward', 'using', 'via', 'based', 'approach'
}

def clean_text(s):
    if not s:
        return ""
    s = re.sub(r'[{}]', '', s)
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

def extract_pdf_info(filepath):
    # 1. Get page count via pdfinfo
    num_pages = 0
    try:
        res = subprocess.run(['pdfinfo', filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        for line in res.stdout.split('\n'):
            if line.startswith('Pages:'):
                num_pages = int(line.split(':')[1].strip())
                break
    except Exception as e:
        print(f"pdfinfo error on {filepath}: {e}")

    # 2. Extract text from first 5 pages via pdftotext
    text = ""
    try:
        res = subprocess.run(['pdftotext', '-l', '5', filepath, '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        text = res.stdout
    except Exception as e:
        print(f"pdftotext error on {filepath}: {e}")

    return num_pages, text

def extract_author_last_names(author_str):
    if not author_str:
        return []
    cleaned = clean_text(author_str)
    # Split by ' and '
    authors = re.split(r'\s+and\s+', cleaned, flags=re.I)
    last_names = []
    for a in authors:
        a = a.strip()
        if not a or a.lower() == 'others':
            continue
        if ',' in a:
            ln = a.split(',')[0].strip()
        else:
            ln = a.split()[-1].strip()
        ln = re.sub(r'[^\w]', '', ln)
        if len(ln) > 1:
            last_names.append(ln)
    return last_names

def tokenize_title(title_str):
    cleaned = clean_text(title_str).lower()
    words = re.findall(r'[a-z0-9]{3,}', cleaned)
    sig_words = [w for w in words if w not in STOP_WORDS]
    return sig_words

KNOWN_SCANNED_BOOKS = {
    'Schumpeter1934': 'The Theory of Economic Development (DLI scan, 782 pages)',
    'Schumpeter1939': 'Business Cycles (DLI scan, 50 pages excerpt)',
    'Osborn1953': 'Applied Imagination (DLI scan, 298 pages)',
    'Bono1967': 'The Use of Lateral Thinking (Edward de Bono, unencrypted)',
}

def verify_all_pdfs():
    entries = parse_bib_file(BIB_PATH)
    
    # Map by key
    seen = {}
    unique_entries = []
    for e in entries:
        k = e['key']
        if k in seen:
            suffix = 2
            while f"{k}_{suffix}" in seen:
                suffix += 1
            e['key'] = f"{k}_{suffix}"
        seen[e['key']] = e
        unique_entries.append(e)

    report = []
    
    for entry in unique_entries:
        key = entry['key']
        fields = entry['fields']
        title = clean_text(fields.get('title', ''))
        authors = clean_text(fields.get('author', ''))
        doi = fields.get('doi', '').strip()
        eprint = fields.get('eprint', '').strip()
        year = fields.get('year', '').strip()
        
        pdf_path = os.path.join(PDF_DIR, f"{key}.pdf")
        if not os.path.exists(pdf_path):
            report.append({
                'key': key,
                'status': 'MISSING',
                'confidence': 'NONE',
                'title': title,
                'authors': authors,
                'year': year,
                'pages': 0,
                'size_kb': 0,
                'details': 'File does not exist (placeholder)'
            })
            continue

        size_kb = os.path.getsize(pdf_path) / 1024
        num_pages, pdf_text = extract_pdf_info(pdf_path)
        pdf_lower = pdf_text.lower()
        
        # 1. Title keyword matching
        title_tokens = tokenize_title(title)
        matched_tokens = [w for w in title_tokens if w in pdf_lower]
        title_ratio = len(matched_tokens) / len(title_tokens) if title_tokens else 1.0

        # 2. Author matching
        last_names = extract_author_last_names(authors)
        matched_authors = [ln for ln in last_names if ln.lower() in pdf_lower]
        author_ratio = len(matched_authors) / len(last_names) if last_names else 1.0

        # 3. DOI / eprint matching
        doi_found = bool(doi and doi.lower() in pdf_lower)
        eprint_found = bool(eprint and eprint.lower() in pdf_lower)

        # Verification classification
        is_verified = False
        confidence = "LOW"
        reasons = []

        if title_ratio >= 0.5:
            reasons.append(f"Title: {len(matched_tokens)}/{len(title_tokens)} keywords matched ({title_ratio*100:.0f}%)")
        if author_ratio >= 0.25:
            reasons.append(f"Authors: {matched_authors}")
        if doi_found:
            reasons.append("DOI matched in text")
        if eprint_found:
            reasons.append("arXiv ID matched in text")

        if key in KNOWN_SCANNED_BOOKS:
            is_verified = True
            confidence = "HIGH (SCANNED BOOK)"
            reasons.append(KNOWN_SCANNED_BOOKS[key])
        elif (title_ratio >= 0.5 and (author_ratio >= 0.25 or doi_found or eprint_found or len(title_tokens) >= 3)) or \
           (doi_found or eprint_found) or \
           (author_ratio >= 0.6 and title_ratio >= 0.33) or \
           (title_ratio >= 0.67):
            is_verified = True
            confidence = "HIGH" if (title_ratio >= 0.6 and (author_ratio >= 0.3 or doi_found or eprint_found)) else "MEDIUM"
        elif num_pages > 0 and (author_ratio >= 0.5 or title_ratio >= 0.4):
            is_verified = True
            confidence = "MEDIUM"
        else:
            is_verified = False
            confidence = "UNCERTAIN"

        report.append({
            'key': key,
            'status': 'VERIFIED' if is_verified else 'FLAGGED',
            'confidence': confidence,
            'title': title,
            'authors': authors,
            'year': year,
            'pages': num_pages,
            'size_kb': size_kb,
            'title_matched': f"{len(matched_tokens)}/{len(title_tokens)}",
            'matched_tokens': matched_tokens,
            'missing_tokens': [w for w in title_tokens if w not in matched_tokens],
            'authors_matched': f"{len(matched_authors)}/{len(last_names)}",
            'matched_authors': matched_authors,
            'reasons': reasons,
            'sample_pdf_text': ' '.join(pdf_text.split()[:40]) if pdf_text else '[No OCR text - Scanned image pages]'
        })

    return report

if __name__ == '__main__':
    rep = verify_all_pdfs()
    verified_count = sum(1 for r in rep if r['status'] == 'VERIFIED')
    flagged = [r for r in rep if r['status'] != 'VERIFIED']
    
    print(f"\n================ VERIFICATION SUMMARY ================")
    print(f"Total entries checked: {len(rep)}")
    print(f"Successfully Verified: {verified_count}")
    print(f"Flagged / Need Review: {len(flagged)}")
    print(f"=======================================================\n")

    if flagged:
        print("Flagged Items:")
        for f in flagged:
            print(f"[{f['key']}] Status: {f['status']} (Confidence: {f.get('confidence')})")
            print(f"  Title: {f['title']}")
            print(f"  Authors: {f['authors']}")
            print(f"  Pages: {f.get('pages')}, Size: {f.get('size_kb', 0):.1f} KB")
            print(f"  Title Matched: {f.get('title_matched')}, Missing: {f.get('missing_tokens')}")
            print(f"  Authors Matched: {f.get('authors_matched')}")
            print(f"  Sample text: {f.get('sample_pdf_text', '')[:150]}")
            print("-" * 50)

    with open('/home/marc/IM-LLM/references/verification_report.json', 'w') as out_f:
        json.dump(rep, out_f, indent=2)
