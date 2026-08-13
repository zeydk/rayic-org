import re
import os

filepath = "../frontend/src/components/AdInputParser.tsx"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
content = re.sub(
    r'(import MapLocationPicker, \{ DISTRICT_COORDS \} from "\./MapLocationPicker";)',
    r'\1\nimport dynamic from "next/dynamic";\nimport TkgmAttributeModal from "./TkgmAttributeModal";\n\nconst LeafletPolygonMap = dynamic(() => import("./LeafletPolygonMap"), {\n  ssr: false,\n  loading: () => (\n    <div className="w-full h-full flex items-center justify-center bg-slate-100">\n      <span className="text-sm font-mono animate-pulse">Harita Yükleniyor...</span>\n    </div>\n  )\n});',
    content
)

# 2. State Additions
content = re.sub(
    r'(const \[fullAddress, setFullAddress\] = useState\(""\);)',
    r'\1\n  const [street, setStreet] = useState("");\n  const [doorNo, setDoorNo] = useState("");\n  const [aptNo, setAptNo] = useState("");\n  const [polygonGeoJson, setPolygonGeoJson] = useState<any>(null);\n  const [isModalOpen, setIsModalOpen] = useState(false);',
    content
)

# 3. Payload
content = re.sub(
    r'(neighborhood,\n\s*full_address: fullAddress)',
    r'\1,\n            street,\n            door_no: doorNo,\n            apt_no: aptNo',
    content
)

# 4. Polygon Geometry
content = re.sub(
    r'(setPinLng\(tkgmInfo\.precise_lng\);)',
    r'\1\n            setPolygonGeoJson(tkgmInfo.polygon_geometry);',
    content
)

# 5. Sorting Districts
content = re.sub(
    r'(Object\.keys\(ISTANBUL_DISTRICTS\))\.map\(\(dist\)',
    r'\1.sort((a,b) => a.localeCompare(b, "tr")).map((dist)',
    content
)
content = re.sub(
    r'(\(ISTANBUL_DISTRICTS\[district\] \|\| \[\]\))\.map\(\(neigh\)',
    r'\1.sort((a,b) => a.localeCompare(b, "tr")).map((neigh)',
    content
)

# 6. Replace Address Field with 3 fields
new_inputs = """<div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Sokak / Cadde İsmi <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  placeholder="Örn: Mehmet Ertem Alp"
                  value={street}
                  onChange={(e) => setStreet(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Kapı No <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  placeholder="Örn: 9"
                  value={doorNo}
                  onChange={(e) => setDoorNo(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Daire No (Opsiyonel)</label>
                <input
                  type="text"
                  placeholder="Örn: 4"
                  value={aptNo}
                  onChange={(e) => setAptNo(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                />
              </div>
            </div>"""

content = re.sub(
    r'<textarea.*?setFullAddress.*?/>',
    new_inputs,
    content,
    flags=re.DOTALL
)

# 7. Add Modal Component at the bottom
modal_replacement = """
      <TkgmAttributeModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        ada={adaNo}
        parsel={parselNo}
        ilce={district}
        mahalle={neighborhood}
        nitelik={nitelik}
        pafta={paftaNo}
        bbList={bbList}
      />
    </div>
  );
}"""

content = re.sub(
    r'</div>\n  \);\n}',
    modal_replacement,
    content
)

# 8. Add Info Icon to open Modal (inside TKGM Header)
tkgm_header_replacement = """<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5E7EB] pb-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-[#047857]" />
                    <span className="text-xs font-extrabold text-[#111827] uppercase">
                      TKGM RESMİ TAŞINMAZ ÖZNİTELİK BİLGİSİ
                    </span>
                    <button onClick={() => setIsModalOpen(true)} className="ml-2 bg-[#047857] text-white px-2.5 py-1 rounded-md text-[10px] uppercase font-bold hover:bg-emerald-700 transition">
                      Öznitelik Bilgisini Göster
                    </button>
                  </div>"""
                  
content = re.sub(
    r'<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-\[#E5E7EB\] pb-3">.*?TKGM RESMİ TAŞINMAZ ÖZNİTELİK BİLGİSİ\s*</span>\s*</div>',
    tkgm_header_replacement,
    content,
    flags=re.DOTALL
)

# 9. Replace MapLocationPicker in Step 1.2
map_replacement = """<div className="space-y-2 mt-4">
                <div className="flex items-center justify-between text-xs font-bold text-[#111827]">
                  <div className="flex items-center space-x-1.5">
                    <MapPin className="w-4 h-4 text-[#047857]" />
                    <span>HARİTADAN BİNANIZIN HASSAS KONUMUNU İĞNE İLE DÜZELTİN <span className="text-red-500">*</span></span>
                  </div>
                  <span className="text-[11px] font-mono text-[#047857] bg-white px-2 py-0.5 border border-[#E5E7EB] rounded-md">
                    Hassas Konum: {pinLat?.toFixed(4)}, {pinLng?.toFixed(4)}
                  </span>
                </div>
                <div className="h-72 w-full border-2 border-[#111827] rounded-2xl relative overflow-hidden bg-[#FAF8F5] shadow-inner">
                  <LeafletPolygonMap
                    lat={pinLat || 40.9483}
                    lng={pinLng || 29.1303}
                    polygonGeoJson={polygonGeoJson}
                    zoom={19}
                  />
                  <div className="absolute top-2 left-2 z-20 bg-[#111827] text-white px-3 py-1 rounded-lg text-xs font-mono font-bold shadow-md">
                    {district} / {neighborhood} (Kadastro Parsel Sınırı)
                  </div>
                </div>
              </div>"""

content = re.sub(
    r'<MapLocationPicker.*?/>',
    map_replacement,
    content,
    flags=re.DOTALL
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("AdInputParser.tsx refactored.")
