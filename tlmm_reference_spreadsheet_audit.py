#!/usr/bin/env python3
"""Audit the published TLMM ESM workbook without changing the model.

The Springer supplementary file is occasionally served through different CDN
hosts. Try only official Springer/SpringerNature endpoints, record the complete
HTTP provenance, and parse the workbook if a real XLSX ZIP is returned.
Failure to retrieve the binary is reported as BLOCKED rather than silently
substituting a third-party reconstruction.
"""
from __future__ import annotations

import io
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

FILENAME = "13157_2019_1229_MOESM1_ESM.xlsx"
DOI = "10.1007/s13157-019-01229-9"
URLS = [
    "https://media.springernature.com/original/springer-static/esm/art%3A10.1007%2Fs13157-019-01229-9/MediaObjects/" + FILENAME,
    "https://static-content.springer.com/esm/art%3A10.1007%2Fs13157-019-01229-9/MediaObjects/" + FILENAME,
    "https://link.springer.com/content/pdf/10.1007/s13157-019-01229-9/MediaObjects/" + FILENAME,
]
REFERER = "https://link.springer.com/article/10.1007/s13157-019-01229-9"
OUT = Path("tlmm_reference_spreadsheet_audit.json")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def shared_strings(zf: zipfile.ZipFile):
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(t.text or "" for t in si.iterfind(".//m:t", NS))
            for si in root.findall("m:si", NS)]


def workbook_sheets(zf: zipfile.ZipFile):
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels.findall("p:Relationship", NS)}
    out=[]
    for s in wb.findall(".//m:sheet", NS):
        rid=s.attrib[f"{{{NS['r']}}}id"]
        target=relmap[rid]
        if target.startswith("/"):
            path=target.lstrip("/")
        elif target.startswith("xl/"):
            path=target
        else:
            path="xl/"+target.lstrip("/")
        out.append((s.attrib["name"], path))
    return out


def cell_records(zf, path, sst):
    root=ET.fromstring(zf.read(path))
    rows=[]
    for c in root.findall(".//m:c", NS):
        ref=c.attrib.get("r"); typ=c.attrib.get("t")
        f=c.find("m:f", NS); v=c.find("m:v", NS)
        formula=(f.text if f is not None else None)
        raw=(v.text if v is not None else None); value=raw
        if typ=="s" and raw is not None:
            try: value=sst[int(raw)]
            except Exception: pass
        elif typ=="inlineStr":
            value="".join(t.text or "" for t in c.iterfind(".//m:t", NS))
        rows.append({"cell":ref,"type":typ,"formula":formula,"cached_or_literal":value})
    return rows


def try_download():
    attempts=[]
    headers={
        "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36",
        "Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*;q=0.8",
        "Referer":REFERER,
    }
    for url in URLS:
        rec={"requested_url":url}
        try:
            req=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(req,timeout=60) as r:
                data=r.read()
                rec.update({"http_status":getattr(r,"status",None),"final_url":r.geturl(),
                            "content_type":r.headers.get("Content-Type"),
                            "content_length_header":r.headers.get("Content-Length"),
                            "download_bytes":len(data),"first_32_hex":data[:32].hex()})
            is_zip=data.startswith(b"PK\x03\x04")
            rec["xlsx_zip_signature"]=is_zip
            attempts.append(rec)
            if is_zip:
                return data,attempts,url
            rec["body_preview_utf8"]=data[:500].decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            body=e.read(500)
            rec.update({"error":"HTTPError","http_status":e.code,"reason":str(e.reason),
                        "content_type":e.headers.get("Content-Type") if e.headers else None,
                        "body_preview_utf8":body.decode("utf-8","replace")})
            attempts.append(rec)
        except Exception as e:
            rec.update({"error":type(e).__name__,"message":str(e)})
            attempts.append(rec)
    return None,attempts,None


def main():
    data,attempts,successful_url=try_download()
    if data is None:
        result={"status":"BLOCKED_REMOTE_TLMM_ESM_ACCESS","doi":DOI,"filename":FILENAME,
                "official_urls_tried":URLS,"attempts":attempts,
                "interpretation":"No non-official substitute was used. Paper-text equations remain the authoritative implementation source until the binary ESM can be audited."}
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        sst=shared_strings(zf); sheets=[]; formula_hits=[]
        for name,path in workbook_sheets(zf):
            cells=cell_records(zf,path,sst)
            formulas=[x for x in cells if x["formula"]]
            literals=[x for x in cells if x["cached_or_literal"] not in (None,"") and not x["formula"]]
            sheets.append({"name":name,"path":path,"n_cells":len(cells),"n_formulas":len(formulas)})
            for x in formulas:
                fx=x["formula"] or ""
                if re.search(r"LOG|POWER|\^|IF|MIN|MAX|10",fx,re.I):
                    formula_hits.append({"sheet":name,**x})
            safe=re.sub('[^A-Za-z0-9]+','_',name).strip('_') or 'sheet'
            Path(f"tlmm_esm_{safe}.json").write_text(
                json.dumps({"sheet":name,"formulas":formulas,"literals":literals},ensure_ascii=False,indent=2),encoding="utf-8")
    result={"status":"PASS_TLMM_ESM_DOWNLOAD_AND_OOXML_AUDIT","doi":DOI,"source_url":successful_url,
            "download_bytes":len(data),"attempts":attempts,"sheets":sheets,"formula_hits":formula_hits}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
