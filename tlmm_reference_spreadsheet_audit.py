#!/usr/bin/env python3
"""Audit the published TLMM ESM workbook without changing the model.

Downloads the exact Springer ESM1 workbook for Keddy & Campbell (2020),
extracts sheet names, cell formulas, cached values and nearby literal labels via
OOXML, and writes a compact JSON audit. This is reference provenance only.
"""
from __future__ import annotations

import json
import re
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

URL = (
    "https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1007%2Fs13157-019-01229-9/MediaObjects/"
    "13157_2019_1229_MOESM1_ESM.xlsx"
)
OUT = Path("tlmm_reference_spreadsheet_audit.json")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def shared_strings(zf: zipfile.ZipFile):
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out=[]
    for si in root.findall("m:si", NS):
        out.append("".join(t.text or "" for t in si.iterfind(".//m:t", NS)))
    return out


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
        ref=c.attrib.get("r")
        typ=c.attrib.get("t")
        f=c.find("m:f", NS)
        v=c.find("m:v", NS)
        formula=(f.text if f is not None else None)
        raw=(v.text if v is not None else None)
        value=raw
        if typ=="s" and raw is not None:
            try: value=sst[int(raw)]
            except Exception: pass
        elif typ=="inlineStr":
            value="".join(t.text or "" for t in c.iterfind(".//m:t", NS))
        rows.append({"cell":ref,"type":typ,"formula":formula,"cached_or_literal":value})
    return rows


def main():
    req=urllib.request.Request(URL, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data=r.read()
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as tf:
        tf.write(data); tf.flush()
        with zipfile.ZipFile(tf.name) as zf:
            sst=shared_strings(zf)
            sheets=[]
            formula_hits=[]
            for name,path in workbook_sheets(zf):
                cells=cell_records(zf,path,sst)
                formulas=[x for x in cells if x["formula"]]
                literals=[x for x in cells if x["cached_or_literal"] not in (None,"") and not x["formula"]]
                sheets.append({"name":name,"path":path,"n_cells":len(cells),"n_formulas":len(formulas)})
                for x in formulas:
                    fx=x["formula"] or ""
                    if re.search(r"LOG|POWER|\^|IF|MIN|MAX|10",fx,re.I):
                        formula_hits.append({"sheet":name,**x})
                # retain every formula for the small published workbook, plus labels, to make provenance auditable
                Path(f"tlmm_esm_{re.sub('[^A-Za-z0-9]+','_',name).strip('_') or 'sheet'}.json").write_text(
                    json.dumps({"sheet":name,"formulas":formulas,"literals":literals},ensure_ascii=False,indent=2),
                    encoding="utf-8")
    result={"status":"PASS_TLMM_ESM_DOWNLOAD_AND_OOXML_AUDIT","source_url":URL,"download_bytes":len(data),"sheets":sheets,"formula_hits":formula_hits}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
