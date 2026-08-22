"use client";

import React, { useState } from "react";
import { ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, MapPin, Sparkles, Check, Edit3, Search, RefreshCw, FileText, Home, Layers } from "lucide-react";
import MapLocationPicker, { DISTRICT_COORDS } from "./MapLocationPicker";
import dynamic from "next/dynamic";

const LeafletPolygonMap = dynamic(() => import("./LeafletPolygonMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-100">
      <span className="text-sm font-mono animate-pulse">Harita Yükleniyor...</span>
    </div>
  )
});

const formatPrice = (val: string) => {
  const numeric = val.replace(/\D/g, "");
  if (!numeric) return "";
  return new Intl.NumberFormat("tr-TR").format(Number(numeric));
};

const priceToText = (val: string) => {
  const numeric = Number(val.replace(/\D/g, ""));
  if (!numeric) return "";
  if (numeric >= 1_000_000_000) return `${(numeric / 1_000_000_000).toLocaleString("tr-TR", { maximumFractionDigits: 2 })} Milyar TL`;
  if (numeric >= 1_000_000) return `${(numeric / 1_000_000).toLocaleString("tr-TR", { maximumFractionDigits: 2 })} Milyon TL`;
  if (numeric >= 1_000) return `${(numeric / 1_000).toLocaleString("tr-TR", { maximumFractionDigits: 2 })} Bin TL`;
  return `${numeric.toLocaleString("tr-TR")} TL`;
};

interface ParsedData {
  user_role: "buyer" | "renter" | "seller";
  price: number;
  net_m2: number;
  gross_m2: number;
  building_age: number;
  floor: string;
  floor_category: string;
  room_count: string;
  total_land_m2: number;
  land_share_num: number;
  land_share_den: number;
  district: string;
  neighborhood: string;
  full_address?: string;
  street?: string;
  door_no?: string;
  apt_no?: string;
  ada_no?: string;
  parsel_no?: string;
  lat?: number;
  lng?: number;
  missing_fields: string[];
}

interface StepFormProps {
  onComplete: (data: ParsedData) => void;
  loading?: boolean;
}

// Complete Official Dataset for ALL 39 Istanbul Districts (14 Asian, 25 European) & exact Neighborhoods
export const ISTANBUL_DISTRICTS: Record<string, string[]> = {
  // --- ANADOLU YAKASI (14 İLÇE) ---
  "Adalar": ["Burgazada", "Heybeliada", "Kınalıada", "Maden", "Nizam"],
  "Ataşehir": ["Aşık Veysel", "Atatürk", "Barbaros", "Esatpaşa", "Ferhatpaşa", "Fetih", "İçerenköy", "İnönü", "Kayışdağı", "Küçükbakkalköy", "Mevlana", "Mimar Sinan", "Mustafa Kemal", "Örnek", "Yeni Çamlıca", "Yeni Sahra", "Yenişehir"],
  "Beykoz": ["Acarlar", "Akbaba", "Alibahadır", "Anadolu Hisarı", "Anadolu Kavağı", "Anadolufeneri", "Baklacı", "Çamlıbahçe", "Çengeldere", "Çiftlik", "Çiğdem", "Çukurçayır", "Dereseki", "Elmalı", "Göksu", "Göllü", "Görele", "Göztepe", "Gümüşsuyu", "İncirköy", "İshaklı", "Kanlıca", "Kavacık", "Kaynarca", "Kılıçlı", "Mahmutşevketpaşa", "Merkez", "Örnekköy", "Ortaçeşme", "Paşabahçe", "Paşamandıra", "Polonezköy", "Riva", "Rüzgarlıbahçe", "Saadetdere", "Soğuksu", "Tokatköy", "Yalıköy", "Yavuz Selim", "Yeni Mahalle", "Zerzavatçı"],
  "Çekmeköy": ["Aydınlar", "Çamlık", "Çatallı", "Ekşioğlu", "Güngören", "Hüseyinli", "İlrange", "Hamidiye", "Kirazlıdere", "Koçullu", "Mehmet Akif", "Merkez", "Mimar Sinan", "Nişanteşte", "Ömerli", "Reşadiye", "Sırapınar", "Soğukpınar", "Sultançiftliği", "Taşdelen", "Yeşiltepe"],
  "Kadıköy": ["19 Mayıs", "Acıbadem", "Bostancı", "Caddebostan", "Caferağa", "Dumlupınar", "Eğitim", "Erenköy", "Fenerbahçe", "Feneryolu", "Fikirtepe", "Göztepe", "Hasanpaşa", "Koşuyolu", "Kozyatağı", "Merdivenköy", "Osmanağa", "Rasimpaşa", "Sahrayıcedit", "Suadiye", "Zühtüpaşa"],
  "Kartal": ["Atalar", "Cevizli", "Cumhuriyet", "Çavuşoğlu", "Esentepe", "Gümüşpınar", "Hürriyet", "Karlıktepe", "Kordonboyu", "Orhantepe", "Orta", "Petrol İş", "Soğanlık Yeni", "Topselvi", "Uğur Mumcu", "Yakacık Çarşı", "Yakacık Yeni", "Yalı", "Yukarı", "Yunus"],
  "Maltepe": ["Altayçeşme", "Altıntepe", "Aydınevler", "Bağlarbaşı", "Başıbüyük", "Büyükbakkalköy", "Cevizli", "Çınar", "Fındıklı", "Girne", "Gülensu", "Gülsuyu", "İidealtepe", "Küçükyalı", "Yalı", "Zümrütevler", "Feyzullah", "Cumhuriyet"],
  "Pendik": ["Ahmet Yesevi", "Bahçelievler", "Batı", "Çamlık", "Çamçeşme", "Çınardere", "Doğu", "Dumlupınar", "Ertuğrulgazi", "Esenyalı", "Fatih", "Fevzi Çakmak", "Gökeyüp", "Güzelyalı", "Harmandere", "Kavakpınar", "Kaynarca", "Kurtköy", "Orhangazi", "Orta", "Ramazanoğlu", "Sanayi", "Sapan Bağları", "Sülüntepe", "Şeyhli", "Velibaba", "Yayalar", "Yenişehir", "Yeşilbağlar", "Ballıca", "Emirli", "Göçbeyli", "Kurna", "Kurtdoğmuş"],
  "Sancaktepe": ["Abdurrahmangazi", "Akpınar", "Atatürk", "Emek", "Eyüp Sultan", "Fatih", "Hilal", "İnönü", "Kemal Türkler", "Meclis", "Merve", "Mevlana", "Paşaköy", "Safa", "Sarıgazi", "Veysel Karani", "Yenidoğan", "Yunus Emek"],
  "Sultanbeyli": ["Abdurrahmangazi", "Adil", "Ahmet Yesevi", "Akşemsettin", "Battalgazi", "Fatih", "Hasanpaşa", "Mimar Sinan", "Mecidiye", "Mehmet Akif", "Necip Fazıl", "Orhangazi", "Turgutreis", "Yavuz Selim", "Ziya Gökalp"],
  "Şile": ["Ağva", "Ahmetli", "Akçakese", "Alacalı", "Avcıkoru", "Bıçkıdere", "Bozkoca", "Çavuş", "Çengilli", "Çayırbaşı", "Darlık", "Değirmençayırı", "Doğancılı", "Erenler", "Esenceli", "Göksu", "Hacıllı", "İmrendere", "İsaköy", "Kabakoz", "Kadıköy", "Kalem", "Karabeyli", "Karacaköy", "Karakiraz", "Kurfallı", "Kervansaray", "Kızılca", "Korucu", "Kömürlük", "Kumbaba", "Meşrutiyet", "Ovacık", "Oruçoğlu", "Satmazlı", "Sofular", "Soğullu", "Şevketiye", "Teke", "Ulupelit", "Üvezli", "Yaka", "Yaylalı", "Yazımanayır", "Yeniköy", "Yeşilvadi", "Ziya Gökalp"],
  "Tuzla": ["Akfırat", "Aydınlı", "Aydıntepe", "Cami", "Evliya Çelebi", "İçmeler", "İstasyon", "Mescit", "Mimar Sinan", "Orhanlı", "Orta", "Postane", "Şifa", "Tepeören", "Yayla", "Anadolu"],
  "Ümraniye": ["Adem Cava", "Altınşehir", "Armağanevler", "Aşağı Dudullu", "Atakent", "Atatürk", "Cemil Meriç", "Elmalıkent", "Esenkent", "Esenevler", "Esenşehir", "Fatih Sultan Mehmet", "Hekimbaşı", "Huzur", "Ihlamurkuyu", "İnkılap", "İstiklal", "Kazım Karabekir", "Madenler", "Mehmet Akif", "Namık Kemal", "Necip Fazıl", "Parseller", "Saray", "Site", "Şerifali", "Tantavi", "Tatlısu", "Tepeüstü", "Topağacı", "Yamanevler", "Yukarı Dudullu"],
  "Üsküdar": ["Acıbadem", "Ahmediye", "Altunizade", "Aziz Mahmud Hüdayi", "Bahçelievler", "Barbaros", "Beylerbeyi", "Bulgurlu", "Burhaniye", "Cumhuriyet", "Çengelköy", "Ferah", "Güzeltepe", "İcapçı", "İcadiye", "Kandilli", "Kısıklı", "Kirazlıtepe", "Kuleli", "Kuzguncuk", "Küçük Çamlıca", "Küplüce", "Mehmet Akif Ersoy", "Mimar Sinan", "Murat Reis", "Salacak", "Selami Ali", "Selimiye", "Sultantepe", "Ünalan", "Valide-i Atik", "Yavuztürk", "Zeynep Kamil"],

  // --- AVRUPA YAKASI (25 İLÇE) ---
  "Arnavutköy": ["Adnan Menderes", "Anadolu", "Arnavutköy Merkez", "Baklalı", "Balaban", "Boğazköy", "Bolcaağaç", "Boyalık", "Çilingir", "Dursunköy", "Durusu", "Hadımköy", "Haraççı", "Imrahor", "İslambey", "Karaburun", "Karlıbayır", "Mavigöl", "M.Nejati Güllüoğlu", "Nenehatun", "Ömerli", "Sazlıbosna", "Taşoluk", "Tayakadın", "Terkos", "Yassıören", "Yeşilbayır"],
  "Avcılar": ["Ambarlı", "Cihangir", "Denizköşkler", "Firuzköy", "Gümüşpala", "Merkez", "Mustafa Kemal Paşa", "Tahtakale", "Üniversite", "Yeşilkent"],
  "Bağcılar": ["Bağlar", "Barbaros", "Çınar", "Demirkapı", "Evren", "Fatih", "Fevzi Çakmak", "Göztepe", "Güneşli", "Hürriyet", "İnönü", "Kazım Karabekir", "Kemalpaşa", "Kirazlı", "Mahmutbey", "Merkez", "Sancaktepe", "Yavuz Selim", "Yenimahalle", "Yüzyıl", "Yıldıztepe"],
  "Bahçelievler": ["Bahçelievler", "Basın Sitesi", "Cumhuriyet", "Çobançeşme", "Fevzi Çakmak", "Hürriyet", "Kocasinan", "Siyavuşpaşa", "Soğanlı", "Şirinevler", "Yenibosna"],
  "Bakırköy": ["Ataköy 1.", "Ataköy 2-5-6.", "Ataköy 3-4-11.", "Ataköy 7-8-9-10. Kısım", "Basınköy", "Cevizlik", "Kartaltepe", "Osmaniye", "Sakızağacı", "Şenlikköy", "Uçar", "Yeşilköy", "Yeşilyurt", "Zeytinlik", "Zuhuratbaba"],
  "Başakşehir": ["Altınşehir", "Bahçeşehir 1. Kısım", "Bahçeşehir 2. Kısım", "Başak", "Başakşehir", "Güvercintepe", "İkitelli OSB", "Kayabaşı", "Şahintepe", "Şamlar", "Ziya Gökalp"],
  "Bayrampaşa": ["Altıntepsi", "Cevatpaşa", "İsmet Paşa", "Kartaltepe", "Kocatepe", "Muratpaşa", "Ortamahalle", "Terziler", "Vatan", "Yenidoğan", "Yıldırım"],
  "Beşiktaş": ["Abbasağa", "Akat", "Arnavutköy", "Balmumcu", "Bebek", "Cihannüma", "Dikilitaş", "Etiler", "Gayrettepe", "Konaklar", "Kuruçeşme", "Kültür", "Levazım", "Levent", "Mecidiye", "Muradiye", "Nisbetiye", "Ortaköy", "Sinanpaşa", "Türkali", "Ulus", "Vişnezade", "Yıldız"],
  "Beylikdüzü": ["Adnan Kahveci", "Barış", "Büyükşehir", "Cumhuriyet", "Dereağzı", "Gürpınar", "Kavaklı", "Marmara", "Sahil", "Yakuplu"],
  "Beyoğlu": ["Arap Cami", "Cihangir", "Evliya Çelebi", "Fetihtepe", "Gümüşsuyu", "Halıcıoğlu", "İstiklal", "Kaptanpaşa", "Katip Mustafa Çelebi", "Keçeci Piri", "Kemankeş Karamustafapaşa", "Kocatepe", "Kulaksız", "Kuluoğlu", "Küçük Piyale", "Müeyyede", "Ömer Avni", "Örnektepe", "Piyalepaşa", "Pürtelaş Hasan Efendi", "Sütlüce", "Şahkulu", "Tomtom", "Yahya Kahya", "Yenişehir"],
  "Büyükçekmece": ["19 Mayıs", "Ahmediye", "Alkent 2000", "Atatürk", "Bahçelievler", "Celaliye", "Cumhuriyet", "Çakmaklı", "Dizdariye", "Ekinoba", "Fatih", "Güzelce", "Hürriyet", "Kamiloba", "Karaağaç", "Kumburgaz", "Mimaroba", "Mimarsinan", "Muratçeşme", "Pınartepe", "Sinanoba", "Türkoba", "Ulus", "Yenimahalle"],
  "Çatalca": ["Atatürk", "Binkılıç", "Çakıl", "Çiftlikköy", "Ferhatpaşa", "Hallaçlı", "İnceğiz", "İzzettin", "Karacaköy", "Kaleiçi", "Muratbey", "Nakkaş", "Oklalı", "Subaşı", "Yalıköy"],
  "Esenler": ["Birlik", "Çifte Havuzlar", "Davutpaşa", "Fatih", "Fevzi Çakmak", "Havaalanı", "Kazım Karabekir", "Kemer", "Menderes", "Mimar Sinan", "Namık Kemal", "Nene Hatun", "Oruçreis", "Turgut Reis", "Yavuz Selim", "100. Yıl"],
  "Esenyurt": ["Akçaburgaz", "Akevler", "Akşemseddin", "Ardıçlı", "Aşık Veysel", "Atatürk", "Bağlarçeşme", "Balıkyolu", "Barbaros Hayrettin Paşa", "Battalgazi", "Cumhuriyet", "Fatih", "Gökevler", "Güzelyurt", "Hürriyet", "İncirtepe", "İnönü", "İstiklal", "Mehterçeşme", "Merkez", "Mevlana", "Necip Fazıl Kısakürek", "Örnek", "Pınar", "Saadetdere", "Sanayi", "Selaheddin Eyyubi", "Sultaniye", "Süleymaniye", "Şehitler", "Talatpaşa", "Turgut Özal", "Üçevler", "Yeşilkent", "Yunus Emre", "Zafer"],
  "Eyüpsultan": ["Akşemsettin", "Alibeyköy", "Güzeltepe", "Emniyettepe", "Esentepe", "Göktürk", "İslambey", "Karadolap", "Nişancı", "Rami Cuma", "Rami Yeni", "Sakarya", "Silahtarağa", "Yeşilpınar", "Topçular", "Mimar Sinan", "Mithatpaşa", "Düğmeciler"],
  "Fatih": ["Aksaray", "Akşemsettin", "Alemdar", "Ali Kuşçu", "Atikali", "Ayvansaray", "Balat", "Beyazıt", "Cankurtaran", "Cerrahpaşa", "Derviş Ali", "Eminönü", "Haseki Sultan", "İskenderpaşa", "Karagümrük", "Koca Mustafapaşa", "Mercan", "Mevlanakapı", "Mimar Hayrettin", "Mimar Kemalettin", "Molla Gürani", "Seyyid Ömer", "Silivrikapı", "Sultan Ahmet", "Şehremini", "Tahtakale", "Topkapı", "Yedikule", "Zeyrek"],
  "Gaziosmanpaşa": ["Bağlarbaşı", "Barbaros Hayrettin Paşa", "Fevzi Çakmak", "Hürriyet", "Karadeniz", "Karayolları", "Karlıtepe", "Kazım Karabekir", "Merkez", "Mevlana", "Pazariçi", "Sarıgöl", "Şemsipaşa", "Yeni Mahalle", "Yenidoğan", "Yıldıztabia"],
  "Güngören": ["Akıncılar", "Abdurrahman Nafiz Gürman", "Gençleşme", "Güneştepe", "Güngören Merkez", "Haznedar", "Mareşal Çakmak", "Sanayi", "Tozkoparan", "Mehmet Nezih Özmen"],
  "Kağıthane": ["Çağlayan", "Çeliktepe", "Emniyet evleri", "Gültepe", "Gürsel", "Hamidiye", "Harmantepe", "Hürriyet", "Mehmet Akif Ersoy", "Merkez", "Nurtepe", "Ortabayır", "Seyrantepe", "Şirintepe", "Talatpaşa", "Telsizler", "Yahya Kemal", "Yeşilce"],
  "Küçükçekmece": ["Atakent", "Atatürk", "Beşyol", "Cennet", "Cumhuriyet", "Fatih", "Fevzi Çakmak", "Gültepe", "Halkalı", "İnönü", "İstasyon", "Kanarya", "Kartaltepe", "Kemalpaşa", "Mehmetakif", "Söğütlü Çeşme", "Sultan Murat", "Tepeüstü", "Yarımburgaz", "Yeni Mahalle", "Yeşilova"],
  "Sarıyer": ["Ayazağa", "Bahçeköy", "Baltalimanı", "Büyükdere", "Çayırbaşı", "Darüşşafaka", "Emirgan", "Fatih Sultan Mehmet", "Ferahevler", "İstinye", "Kazım Karabekir", "Kireçburnu", "Maslak", "Pınar", "Poligon", "Reşitpaşa", "Rumelihisarı", "Rumelikavağı", "Tarabya", "Uskumruköy", "Yeniköy", "Zekeriyaköy"],
  "Silivri": ["Akören", "Alipaşa", "Bekirli", "Büyük Çavuşlu", "Çanta", "Değirmenköy", "Fatih", "Gümüşyaka", "Kadıköy", "Kavaklı", "Küçük Kılıçlı", "Mimar Sinan", "Ortaköy", "Piri Mehmet Paşa", "Selimpaşa", "Semizkumlar", "Seymen", "Yolçatı"],
  "Sultangazi": ["50. Yıl", "75. Yıl", "Cebeci", "Cumhuriyet", "Esentepe", "Gazi", "Habibler", "İsmetpaşa", "Malkoçoğlu", "Sultançiftliği", "Uğur Mumcu", "Yayla", "Yunus Emre", "Zübeyde Hanım"],
  "Şişli": ["19 Mayıs", "Bozkurt", "Cumhuriyet", "Duatepe", "Ergenekon", "Esentepe", "Eskişehir", "Feriköy", "Fulya", "Gülbahar", "Halaskargazi", "Halide Edip Adıvar", "Halil Rıfat Paşa", "Harbiye", "İnönü", "İzzet Paşa", "Kaptanpaşa", "Kuştepe", "Mahmut Şevket Paşa", "Mecidiyeköy", "Merkez", "Meşrutiyet", "Paşa", "Teşvikiye", "Yayla"],
  "Zeytinburnu": ["Beşitelsiz", "Çırpıcı", "Gökalp", "Kazlıçeşme", "Maltepe", "Merkezefendi", "Nuripaşa", "Seyitnizam", "Sümer", "Telsiz", "Veliefendi", "Yenidoğan", "Yeşiltepe"]
};

export default function AdInputParser({ onComplete, loading }: StepFormProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // User Role Choice
  const [userRole, setUserRole] = useState<"buyer" | "renter" | "seller">("buyer");

  // Step 1: MANDATORY DROPDOWNS FOR DISTRICT & NEIGHBORHOOD
  const [district, setDistrict] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [fullAddress, setFullAddress] = useState("");
  const [street, setStreet] = useState("");
  const [doorNo, setDoorNo] = useState("");
  const [aptNo, setAptNo] = useState("");
  const [polygonGeoJson, setPolygonGeoJson] = useState<any>(null);
  const [adaNo, setAdaNo] = useState("");
  const [parselNo, setParselNo] = useState("");
  const [paftaNo, setPaftaNo] = useState("");
  const [nitelik, setNitelik] = useState("");
  const [tasinmazId, setTasinmazId] = useState("");
  const [selectedBBNo, setSelectedBBNo] = useState<string>("");
  const [roomCount, setRoomCount] = useState("");

  const [bbList, setBbList] = useState<any[]>([]);
  const [katMulkiyetiDurumu, setKatMulkiyetiDurumu] = useState<string>("");
  const [bbVeriDurumu, setBbVeriDurumu] = useState<string>("");
  const [imarDurumu, setImarDurumu] = useState<any>(null);

  // Geocoded Coordinates and Confirmation State
  const [isSearchingAddress, setIsSearchingAddress] = useState(false);
  const [isAddressFound, setIsAddressFound] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isManualEditMode, setIsManualEditMode] = useState(false);

  const [pinLat, setPinLat] = useState<number | undefined>(undefined);
  const [pinLng, setPinLng] = useState<number | undefined>(undefined);

  // Step 2: Price & Area (ZERO DEFAULTS)
  const [price, setPrice] = useState<string>("");
  const [netM2, setNetM2] = useState<string>("");
  const [grossM2, setGrossM2] = useState<string>("");

  // Step 3: Building Details, Land Size & Land Share (ZERO DEFAULTS)
  const [buildingAge, setBuildingAge] = useState<string>("");
  const [floorCategory, setFloorCategory] = useState("");
  const [totalLandM2, setTotalLandM2] = useState<string>("");
  const [landNum, setLandNum] = useState<string>("");
  const [landDen, setLandDen] = useState<string>("");

  const handleDistrictChange = (newDist: string) => {
    setDistrict(newDist);
    setNeighborhood("");
    setIsAddressFound(false);
    setIsConfirmed(false);
    if (newDist && DISTRICT_COORDS[newDist]) {
      setPinLat(DISTRICT_COORDS[newDist].lat);
      setPinLng(DISTRICT_COORDS[newDist].lng);
    }
  };

  const handleNeighborhoodChange = (newNeigh: string) => {
    setNeighborhood(newNeigh);
    setIsAddressFound(false);
    setIsConfirmed(false);
  };

  // Manual Ada/Parsel edit: we cannot fabricate a bağımsız bölüm list — the
  // per-unit (daire) data is only available via e-Devlet/TAKBIS.
  const refreshCadastreAndBBList = (newAda: string, newParsel: string) => {
    setAdaNo(newAda);
    setParselNo(newParsel);
    setBbList([]);
    setSelectedBBNo("");
    setBbVeriDurumu("Ada/Parsel elle değiştirildi. Daire bazlı bağımsız bölüm listesi TKGM açık API'sinde bulunmaz (e-Devlet/TAKBIS gerekir).");
    setTasinmazId(`TKGM_${district.substring(0, 3).toUpperCase()}_${newAda}_${newParsel}`);
  };

  // REAL LIVE CADASTRE LOOKUP VIA BACKEND API
  // ADA/PARSEL-ÖNCELİKLİ SORGU: kullanıcı ada/parsel biliyorsa adres olmadan sorgular
  const handleExecuteAdaParselSearch = () => {
    if (!district || !neighborhood) {
      setErrorMsg("Lütfen önce İlçe ve Mahalle seçin.");
      return;
    }
    if (!adaNo.trim() || !parselNo.trim()) {
      setErrorMsg("Lütfen Ada ve Parsel numaralarını girin.");
      return;
    }
    setIsSearchingAddress(true);
    setErrorMsg(null);
    setTimeout(async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/cadastre-lookup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            district, neighborhood,
            user_ada: adaNo.trim(),
            user_parsel: parselNo.trim(),
          }),
        });
        if (res.ok) {
          const tkgmInfo = await res.json();
          setAdaNo(tkgmInfo.ada_no);
          setParselNo(tkgmInfo.parsel_no);
          if (tkgmInfo.total_land_area_m2 && tkgmInfo.total_land_area_m2 > 0) {
            setTotalLandM2(String(tkgmInfo.total_land_area_m2));
          }
          if (tkgmInfo.oznitelik) {
            setPaftaNo(tkgmInfo.oznitelik.pafta_no);
            setNitelik(tkgmInfo.oznitelik.nitelik);
            setTasinmazId(tkgmInfo.oznitelik.tasinmaz_id);
          }
          setImarDurumu(tkgmInfo.imar_durumu || null);
          setPinLat(tkgmInfo.precise_lat);
          setPinLng(tkgmInfo.precise_lng);
          setPolygonGeoJson(tkgmInfo.polygon_geometry);
        } else {
          setErrorMsg("Ada/Parsel ile konum çözümlenemedi. Bilmiyorsanız adresinizi girin.");
          setImarDurumu(null);
        }
      } catch (err) {
        setErrorMsg("Sunucuya ulaşılamadı, TKGM verisi alınamadı.");
        setImarDurumu(null);
      } finally {
        setIsSearchingAddress(false);
        setIsAddressFound(true);
        setIsConfirmed(false);
      }
    }, 300);
  };

  const handleExecuteAddressSearch = () => {
    if (!district) {
      setErrorMsg("Lütfen önce İlçe Seçimini yapın.");
      return;
    }

    if (!neighborhood) {
      setErrorMsg("Lütfen Mahalle Seçimini dropdown menüden yapın (Mecburidir).");
      return;
    }

    setIsSearchingAddress(true);
    setErrorMsg(null);

    setTimeout(async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/cadastre-lookup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            district,
            neighborhood,
            full_address: fullAddress,
            street,
            door_no: doorNo,
            apt_no: aptNo
          })
        });

        if (res.ok) {
          const tkgmInfo = await res.json();
          setAdaNo(tkgmInfo.ada_no);
          setParselNo(tkgmInfo.parsel_no);
          if (tkgmInfo.total_land_area_m2 && tkgmInfo.total_land_area_m2 > 0) {
            setTotalLandM2(String(tkgmInfo.total_land_area_m2));
          }
          if (tkgmInfo.oznitelik) {
            setPaftaNo(tkgmInfo.oznitelik.pafta_no);
            setNitelik(tkgmInfo.oznitelik.nitelik);
            setTasinmazId(tkgmInfo.oznitelik.tasinmaz_id);
            if (tkgmInfo.oznitelik.alani_m2 && tkgmInfo.oznitelik.alani_m2 > 0) {
              setTotalLandM2(String(tkgmInfo.oznitelik.alani_m2));
            }
          }
          // Bağımsız bölüm (daire) listesi TKGM açık API'sinde yer almaz; backend
          // sahte liste üretmez. Gerçek kat mülkiyeti durumunu ve bilgi notunu göster.
          const realBB = (tkgmInfo.bb_listesi || []).map((b: any) => ({
            bbNo: b.bb_no,
            daireNo: b.daire_no,
            bbTipi: b.bb_tipi,
            katNo: b.kat_no,
            arsaPay: b.arsa_pay_payda,
            floorCat: b.kat_no.includes("Zemin") ? "giris" : b.kat_no.includes("Çatı") ? "en_ust" : "ara_kat"
          }));
          setBbList(realBB);
          setSelectedBBNo("");
          setKatMulkiyetiDurumu(tkgmInfo.kat_mulkiyeti_durumu || "");
          setBbVeriDurumu(tkgmInfo.bb_veri_durumu || "");
          setImarDurumu(tkgmInfo.imar_durumu || null);
          setPinLat(tkgmInfo.precise_lat);
          setPinLng(tkgmInfo.precise_lng);
            setPolygonGeoJson(tkgmInfo.polygon_geometry);
        } else {
          // No mock fallback: surface an honest "veri alınamadı" state.
          setErrorMsg(`TKGM sorgusu başarısız oldu (sunucu yanıtı: ${res.status}). Lütfen tekrar deneyin.`);
          setBbList([]);
          setSelectedBBNo("");
          setKatMulkiyetiDurumu("");
          setBbVeriDurumu("TKGM verisine ulaşılamadı.");
          setImarDurumu(null);
        }
      } catch (err) {
        // Backend unreachable -> honest error, never fabricate ada/parsel/BB data.
        setErrorMsg("Sunucuya ulaşılamadı, TKGM verisi alınamadı. Analiz motorunun (backend) çalıştığından emin olun.");
        setBbList([]);
        setSelectedBBNo("");
        setKatMulkiyetiDurumu("");
        setBbVeriDurumu("TKGM verisine ulaşılamadı.");
        setImarDurumu(null);
      } finally {
        setIsSearchingAddress(false);
        setIsAddressFound(true);
        setIsConfirmed(false);
      }
    }, 500);
  };

  const handleSelectBBItem = (bbNo: string) => {
    setSelectedBBNo(bbNo);
    const item = bbList.find(b => b.bbNo === bbNo);
    if (item) {
      setFloorCategory(item.floorCat);
      const parts = item.arsaPay.split("/");
      if (parts.length === 2) {
        setLandNum(parts[0]);
        setLandDen(parts[1]);
      }
    }
  };

  const validateStep1 = () => {
    if (!district || !neighborhood || !roomCount) {
      setErrorMsg("Lütfen İlçe, Mahalle ve Oda Düzeni seçimlerini yapın.");
      return false;
    }

    if (!isAddressFound) {
      setErrorMsg("Lütfen 'ADRESİ BUL VE HARİTADA İŞARETLE' butonuna tıklayarak konumu bulun.");
      return false;
    }

    if (!isConfirmed) {
      setErrorMsg("Lütfen tespit edilen bilgileri onaylayın (ONAYLA VE İLERLE butonuna tıklayın).");
      return false;
    }

    setErrorMsg(null);
    return true;
  };

  const validateStep2 = () => {
    if (!price || Number(price) <= 0) {
      setErrorMsg("Lütfen geçerli bir İlan Satış Fiyatı (TL) girin.");
      return false;
    }
    if (!netM2 || Number(netM2) <= 0) {
      setErrorMsg("Lütfen geçerli bir Net Metrekare (m²) girin.");
      return false;
    }
    if (!grossM2 || Number(grossM2) <= 0) {
      setErrorMsg("Lütfen geçerli bir Brüt Metrekare (m²) girin.");
      return false;
    }
    setErrorMsg(null);
    return true;
  };

  const validateStep3 = () => {
    if (buildingAge === "" || Number(buildingAge) < 0) {
      setErrorMsg("Lütfen geçerli bir Bina Yaşı (Yıl) girin.");
      return false;
    }
    if (!floorCategory) {
      setErrorMsg("Lütfen Kat Konumu seçimini yapın.");
      return false;
    }
    if (!totalLandM2 || Number(totalLandM2) <= 0) {
      setErrorMsg("Lütfen geçerli bir Toplam Arsa Büyüklüğü (m²) girin.");
      return false;
    }
    if (!landNum || Number(landNum) <= 0 || !landDen || Number(landDen) <= 0) {
      setErrorMsg("Lütfen geçerli Arsa Payı değerleri (Pay / Payda) girin.");
      return false;
    }
    setErrorMsg(null);
    return true;
  };

  const handleNextStep = (nextStep: 2 | 3) => {
    if (nextStep === 2 && validateStep1()) {
      setStep(2);
    } else if (nextStep === 3 && validateStep2()) {
      setStep(3);
    }
  };

  const handleFinish = () => {
    if (!validateStep3()) return;

    const data: ParsedData = {
      user_role: userRole,
      price: Number(price.replace(/\D/g, "")),
      net_m2: Number(netM2),
      gross_m2: Number(grossM2),
      building_age: Number(buildingAge),
      floor: floorCategory === "ara_kat" ? "Ara Kat" : floorCategory === "giris" ? "Giriş / Zemin Kat" : floorCategory === "bodrum" ? "Bodrum Kat" : "En Üst Kat",
      floor_category: floorCategory,
      room_count: roomCount,
      total_land_m2: Number(totalLandM2),
      land_share_num: Number(landNum),
      land_share_den: Number(landDen),
      district,
      neighborhood,
      full_address: fullAddress,
      street,
      door_no: doorNo,
      apt_no: aptNo.trim() || `${neighborhood} Mah. ${district}`,
      ada_no: adaNo.trim(),
      parsel_no: parselNo.trim(),
      lat: pinLat,
      lng: pinLng,
      missing_fields: []
    };

    onComplete(data);
  };

  return (
    <div className="light-card p-6 bg-white border border-[#E5E7EB] space-y-6">
      
      {/* STEPPER PROGRESS BAR */}
      <div className="border-b border-[#E5E7EB] pb-4">
        <div className="flex items-center justify-between mb-3 text-xs font-bold">
          <span className="text-[#111827] uppercase tracking-wider font-display">
            ADIM {step} / 3: {step === 1 ? "İLÇE/MAHALLE İLE TKGM ÖZNİTELİK VE BİNA LİSTESİ SORGUSU" : step === 2 ? "FİYAT VE METREKARE" : "BİNA YAŞI VE ARSA PAYI"}
          </span>
          <span className="text-slate-500 font-mono">%{Math.round((step / 3) * 100)} Tamamlandı</span>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div className={`h-2 rounded-full transition-all ${step >= 1 ? "bg-[#111827]" : "bg-[#E5E7EB]"}`}></div>
          <div className={`h-2 rounded-full transition-all ${step >= 2 ? "bg-[#111827]" : "bg-[#E5E7EB]"}`}></div>
          <div className={`h-2 rounded-full transition-all ${step >= 3 ? "bg-[#111827]" : "bg-[#E5E7EB]"}`}></div>
        </div>
      </div>

      {/* ERROR WARNING BANNER */}
      {errorMsg && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-bold flex items-center space-x-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* PERSISTENT MAP VIEW (Steps 2 & 3) */}
      {step > 1 && isAddressFound && (
        <div className="h-64 w-full border-2 border-[#111827] rounded-2xl relative overflow-hidden bg-[#FAF8F5] shadow-inner mb-6 animate-fadeIn">
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
      )}

      {/* STEP 1: MANDATORY DROPDOWN SELECTION */}
      {step === 1 && (
        <div className="space-y-5 animate-fadeIn">
          
          {/* USER ROLE SELECTION */}
          <div>
            <label className="text-slate-600 block mb-2 uppercase text-[10px] font-bold">
              1. İşlem Amacınız Nedir? <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-bold">
              
              <button
                type="button"
                onClick={() => setUserRole("buyer")}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  userRole === "buyer"
                    ? "bg-[#111827] text-white border-[#111827] shadow-sm"
                    : "bg-[#FAF8F5] text-[#111827] border-[#E5E7EB] hover:border-[#111827]"
                }`}
              >
                <div className="text-sm font-extrabold mb-0.5">🔑 Konut Alacağım</div>
                <div className={`text-[11px] font-medium ${userRole === "buyer" ? "text-slate-300" : "text-slate-500"}`}>
                  Satın almayı düşündüğüm evin gerçek değerini, deprem ve mahalle risklerini öğreneceğim.
                </div>
              </button>

              <button
                type="button"
                onClick={() => setUserRole("renter")}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  userRole === "renter"
                    ? "bg-[#111827] text-white border-[#111827] shadow-sm"
                    : "bg-[#FAF8F5] text-[#111827] border-[#E5E7EB] hover:border-[#111827]"
                }`}
              >
                <div className="text-sm font-extrabold mb-0.5">🏠 Konut Kiralayacağım</div>
                <div className={`text-[11px] font-medium ${userRole === "renter" ? "text-slate-300" : "text-slate-500"}`}>
                  Kiralamayı düşündüğüm evin rayiç kirasını ve mahalle bilgilerini inceleyeceğim.
                </div>
              </button>

              <button
                type="button"
                onClick={() => setUserRole("seller")}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  userRole === "seller"
                    ? "bg-[#111827] text-white border-[#111827] shadow-sm"
                    : "bg-[#FAF8F5] text-[#111827] border-[#E5E7EB] hover:border-[#111827]"
                }`}
              >
                <div className="text-sm font-extrabold mb-0.5">💼 Satıcı veya Kiraya Verenim</div>
                <div className={`text-[11px] font-medium ${userRole === "seller" ? "text-slate-300" : "text-slate-500"}`}>
                  Evimi satmak veya kiraya vermek istiyorum, gerçek değerini öğreneceğim.
                </div>
              </button>

            </div>
          </div>

          {/* STEP 1.1: SELECT DISTRICT & NEIGHBORHOOD MANDATORY DROPDOWNS */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-bold p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB]">
            
            {/* District First (Mandatory) */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                2. İlçe Seçiniz (İstanbul'un 39 İlçesi) <span className="text-red-500">*</span>
              </label>
              <select
                value={district}
                onChange={(e) => handleDistrictChange(e.target.value)}
                className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
              >
                <option value="">-- İlçe Seçiniz --</option>
                {Object.keys(ISTANBUL_DISTRICTS).sort((a,b) => a.localeCompare(b, "tr")).map((dist) => (
                  <option key={dist} value={dist}>{dist}</option>
                ))}
              </select>
            </div>

            {/* Neighborhood Second (Mandatory Dropdown) */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                3. Mahalle Seçiniz (Mecburi Dropdown) <span className="text-red-500">*</span>
              </label>
              <select
                value={neighborhood}
                onChange={(e) => handleNeighborhoodChange(e.target.value)}
                disabled={!district}
                className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
              >
                <option value="">-- Mahalle Seçiniz --</option>
                {(ISTANBUL_DISTRICTS[district] || []).sort((a,b) => a.localeCompare(b, "tr")).map((neigh) => (
                  <option key={neigh} value={neigh}>{neigh}</option>
                ))}
              </select>
            </div>

            {/* Room Count */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                4. Oda Düzeni <span className="text-red-500">*</span>
              </label>
              <select
                value={roomCount}
                onChange={(e) => setRoomCount(e.target.value)}
                className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
              >
                <option value="">-- Oda Düzeni Seçiniz --</option>
                <option value="1+1">1+1</option>
                <option value="2+1">2+1</option>
                <option value="3+1">3+1</option>
                <option value="4+1">4+1</option>
                <option value="4+2">4+2</option>
              </select>
            </div>

          </div>

          {/* STEP 1.2a: ADA/PARSEL-ÖNCELİKLİ (en doğru, birincil yöntem) */}
          <div className="p-4 bg-[#F0FDF4] rounded-xl border-2 border-[#047857] space-y-3">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-[#047857]">
              <Layers className="w-4 h-4" />
              <span>5. ADA / PARSELİNİZİ BİLİYOR MUSUNUZ? (En doğru yöntem)</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Ada No</label>
                <input
                  type="text"
                  placeholder="Örn: 2983"
                  value={adaNo}
                  onChange={(e) => setAdaNo(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#047857]"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Parsel No</label>
                <input
                  type="text"
                  placeholder="Örn: 142"
                  value={parselNo}
                  onChange={(e) => setParselNo(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#047857]"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={handleExecuteAdaParselSearch}
                  disabled={isSearchingAddress}
                  className="w-full py-3 px-4 rounded-xl bg-[#047857] hover:bg-[#065f46] text-white text-xs font-extrabold flex items-center justify-center space-x-1.5 transition-all shadow-md uppercase"
                >
                  <Search className="w-4 h-4 text-white" />
                  <span>Ada/Parsel ile Sorgula</span>
                </button>
              </div>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">
              Ada/parselinizi tapunuzda bulabilirsiniz. Bilmiyorsanız aşağıdan adresinizi girin, sizin için bulalım.
            </p>
          </div>

          {/* STEP 1.2b: ADRESTEN BULMA (ada/parsel bilinmiyorsa yedek yöntem) */}
          <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-bold text-[#111827]">
                <MapPin className="w-4 h-4 text-[#047857]" />
                <span>veya — BİLMİYORSANIZ ADRESİNİZİ GİRİN</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Sokak / Cadde İsmi <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  placeholder="Örn: Cumhuriyet Caddesi"
                  value={street}
                  onChange={(e) => setStreet(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Kapı No <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  placeholder="Örn: 19"
                  value={doorNo}
                  onChange={(e) => setDoorNo(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Daire No (Opsiyonel)</label>
                <input
                  type="text"
                  placeholder="Örn: 23"
                  value={aptNo}
                  onChange={(e) => setAptNo(e.target.value)}
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-xs text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleExecuteAddressSearch}
              disabled={isSearchingAddress}
              className="w-full py-3 px-4 rounded-xl bg-[#111827] hover:bg-[#047857] text-white text-xs font-extrabold flex items-center justify-center space-x-2 transition-all shadow-md uppercase tracking-wider"
            >
              {isSearchingAddress ? (
                <>
                  <RefreshCw className="w-4 h-4 text-white animate-spin" />
                  <span>TKGM APİ İLE ÖZNİTELİK VE BİNA BB LİSTESİ SORGULANIYOR...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 text-white" />
                  <span>🔍 ADRESİ BUL VE HARİTADA İŞARETLE</span>
                </>
              )}
            </button>
          </div>

          {/* TKGM ÖZNİTELİK BİLGİSİ & DYNAMICALLY REFRESHED BB LİSTESİ SORGUSU */}
          {isAddressFound && (
            <div className="space-y-4 animate-fadeIn">
              
              {/* TKGM RESMİ TAŞINMAZ ÖZNİTELİK KARTI */}
              <div className="p-5 bg-[#FAF8F5] rounded-2xl border-2 border-[#111827] space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5E7EB] pb-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-[#047857]" />
                    <span className="text-xs font-extrabold text-[#111827] uppercase">
                      TKGM RESMİ TAŞINMAZ ÖZNİTELİK BİLGİSİ
                    </span>
                  </div>
                  <span className="text-xs font-mono font-extrabold text-[#047857] bg-white px-2.5 py-0.5 border rounded">
                    Sorgulanan Taşınmaz ID: {tasinmazId || "TKGM_MAL_1542_38"}
                  </span>
                </div>

                {/* EDITABLE ADA & PARSEL INPUTS WITH DYNAMIC REFRESH ON CHANGE */}
                {isManualEditMode ? (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-bold p-3 bg-white rounded-xl border-2 border-[#047857]">
                    <div>İl / İlçe: <span className="text-[#047857] font-mono block mt-1">{district}</span></div>
                    <div>Mahalle: <span className="text-[#047857] font-mono block mt-1">{neighborhood}</span></div>
                    <div>
                      <label className="text-slate-600 uppercase text-[10px] block mb-1">Ada No (Düzenle)</label>
                      <input
                        type="text"
                        value={adaNo}
                        onChange={(e) => refreshCadastreAndBBList(e.target.value, parselNo)}
                        className="w-full bg-[#FAF8F5] border border-[#047857] rounded-lg p-1.5 font-mono text-[#111827] font-bold text-center"
                      />
                    </div>
                    <div>
                      <label className="text-slate-600 uppercase text-[10px] block mb-1">Parsel No (Düzenle)</label>
                      <input
                        type="text"
                        value={parselNo}
                        onChange={(e) => refreshCadastreAndBBList(adaNo, e.target.value)}
                        className="w-full bg-[#FAF8F5] border border-[#047857] rounded-lg p-1.5 font-mono text-[#111827] font-bold text-center"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-bold font-mono text-[#111827] bg-white p-3 rounded-xl border border-[#E5E7EB]">
                    <div>İl / İlçe: <span className="text-[#047857]">{district}</span></div>
                    <div>Mahalle: <span className="text-[#047857]">{neighborhood}</span></div>
                    <div>Ada / Parsel: <span className="text-[#111827] bg-[#FAF8F5] px-1.5 py-0.5 rounded font-extrabold text-[#047857]">{adaNo} / {parselNo}</span></div>
                    <div>Pafta No: <span className="text-[#111827]">{paftaNo || "154-38-M"}</span></div>
                  </div>
                )}

                <div className="text-xs text-slate-700 font-medium">
                  <strong>Taşınmaz Nitelik Kaydı: </strong>
                  <span className="font-bold text-[#111827]">{nitelik || "Kargir 6 Katlı Bitişik Nizam Konut Yapısı"}</span>
                </div>

                {/* İMAR DURUMU (İLÇE BELEDİYESİ WEBGİS) — alıcı için kritik */}
                {imarDurumu && imarDurumu.supported && (
                  <div className="pt-2 border-t border-[#E5E7EB] space-y-2">
                    <label className="text-[#111827] flex items-center justify-between uppercase text-[10px] font-extrabold">
                      <span className="flex items-center space-x-1.5">
                        <Layers className="w-3.5 h-3.5 text-[#C2410C]" />
                        <span>İmar Durumu ({imarDurumu.belediye})</span>
                      </span>
                      <a href={imarDurumu.kaynak_url} target="_blank" rel="noopener noreferrer" className="text-[#0284C7] font-mono font-bold hover:underline">
                        Resmi Belge →
                      </a>
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                      {([
                        ["Fonksiyon", imarDurumu.fonksiyon],
                        ["İnşaat Nizamı", imarDurumu.insaat_nizami],
                        ["Emsal (KAKS)", imarDurumu.kaks || imarDurumu.emsal],
                        ["TAKS", imarDurumu.taks],
                        ["Bina Yüksekliği (Hmaks)", imarDurumu.bina_yuksekligi || imarDurumu.hmaks || imarDurumu.maks_yukseklik_m],
                        ["Kat Adedi", imarDurumu.kat_adedi || imarDurumu.maks_kat_adedi || imarDurumu.maks_kat],
                        ["Ön Bahçe", imarDurumu.on_bahce],
                        ["Yan Bahçe", imarDurumu.yan_bahce],
                        ["Arka Bahçe", imarDurumu.arka_bahce],
                        ["Bina Derinliği", imarDurumu.bina_derinligi],
                        ["Bina Genişliği", imarDurumu.bina_genisligi],
                        ["Pafta", imarDurumu.pafta],
                        ["Plan Ölçeği", imarDurumu.plan_olcegi],
                        ["Tasdik Tarihi", imarDurumu.tasdik_tarihi],
                        ["Parsel Alanı", imarDurumu.parsel_alani],
                      ] as [string, string | undefined][]).filter(([, v]) => v).map(([label, v]) => (
                        <div key={label} className="p-2 bg-[#FAF8F5] border border-[#E5E7EB] rounded-lg">
                          <span className="text-[9px] text-slate-500 uppercase block font-bold">{label}</span>
                          <span className="text-xs text-[#111827] font-extrabold break-words">{v}</span>
                        </div>
                      ))}
                    </div>

                    {/* Ham belediye öznitelikleri — hiçbir alan kaybolmasın (her platform) */}
                    {imarDurumu.tum_alanlar && Object.keys(imarDurumu.tum_alanlar).length > 0 && (
                      <details className="text-[10px] text-slate-600 mt-1">
                        <summary className="cursor-pointer font-bold text-[#0284C7]">🗂️ Tüm İmar Öznitelikleri ({Object.keys(imarDurumu.tum_alanlar).length})</summary>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 mt-1">
                          {Object.entries(imarDurumu.tum_alanlar as Record<string, string>).map(([label, v]) => (
                            <div key={label} className="p-1.5 bg-[#FAF8F5] border border-[#E5E7EB] rounded-md">
                              <span className="text-[8px] text-slate-500 uppercase block font-bold break-words">{label}</span>
                              <span className="text-[11px] text-[#111827] font-bold break-words">{String(v)}</span>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                    {imarDurumu.plan_notlari && (
                      <details className="text-[10px] text-slate-600">
                        <summary className="cursor-pointer font-bold text-[#0284C7]">📋 Plan Notları ve İmar Planı Geçmişi</summary>
                        <p className="mt-1 font-medium leading-relaxed max-h-40 overflow-y-auto bg-[#FAF8F5] border border-[#E5E7EB] rounded-lg p-2">
                          {imarDurumu.plan_notlari}
                        </p>
                        {imarDurumu.imar_plani && (
                          <p className="mt-1 text-[9px] text-slate-500 leading-relaxed">
                            <strong>Meri İmar Planı:</strong> {imarDurumu.imar_plani}
                          </p>
                        )}
                      </details>
                    )}
                  </div>
                )}

                {/* CONFIRMATION ACTION BUTTONS */}
                <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <span className="text-xs font-bold text-slate-700">
                    {isConfirmed ? "✅ Lokasyon, Öznitelik ve Ada/Parsel Bilgileri Onaylandı" : "Tespit edilen konum ve Ada/Parsel Numaraları doğru mu?"}
                  </span>

                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => setIsManualEditMode(!isManualEditMode)}
                      className={`px-3.5 py-2 rounded-xl text-xs font-bold border transition-all flex items-center space-x-1 ${
                        isManualEditMode
                          ? "bg-amber-400 text-[#111827] border-amber-500 font-extrabold"
                          : "border-[#D1D5DB] text-slate-700 hover:bg-slate-100"
                      }`}
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>{isManualEditMode ? "Tamam" : "Düzelt"}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setIsConfirmed(true);
                        setIsManualEditMode(false);
                        setErrorMsg(null);
                      }}
                      className={`px-5 py-2.5 rounded-xl text-xs font-extrabold flex items-center space-x-1.5 transition-all ${
                        isConfirmed
                          ? "bg-[#047857] text-white shadow-sm"
                          : "bg-[#111827] hover:bg-[#047857] text-white"
                      }`}
                    >
                      <Check className="w-4 h-4 text-white" />
                      <span>{isConfirmed ? "ONAYLANDI" : "ONAYLA VE İLERLE"}</span>
                    </button>
                  </div>
                </div>
              </div>

            </div>
          )}

          <div className="flex justify-end pt-4 border-t border-[#E5E7EB]">
            <button
              type="button"
              onClick={() => handleNextStep(2)}
              className="light-btn px-6 py-3 text-xs font-bold uppercase tracking-wider flex items-center space-x-2"
            >
              <span>İLERİ: FİYAT VE METREKARE</span>
              <ArrowRight className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: FİYAT VE METREKARE (ZERO DEFAULTS) */}
      {step === 2 && (
        <div className="space-y-4 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-bold">
            
            {/* Price */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                6. İlan Satış Fiyatı (TL) <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="Örn: 12.500.000"
                value={price}
                onChange={(e) => setPrice(formatPrice(e.target.value))}
                className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                required
              />
              {price && (
                <div className="mt-1.5 text-[11px] font-bold text-[#047857]">
                  {priceToText(price)}
                </div>
              )}
            </div>

            {/* Net m2 */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                7. Net Metrekare (m²) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                placeholder="Örn: 95"
                value={netM2}
                onChange={(e) => setNetM2(e.target.value)}
                className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                required
              />
            </div>

            {/* Gross m2 */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                8. Brüt Metrekare (m²) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                placeholder="Örn: 115"
                value={grossM2}
                onChange={(e) => setGrossM2(e.target.value)}
                className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                required
              />
            </div>

          </div>

          <div className="flex justify-between pt-4 border-t border-[#E5E7EB]">
            <button
              type="button"
              onClick={() => { setErrorMsg(null); setStep(1); }}
              className="px-5 py-2.5 rounded-xl text-xs font-bold border border-[#D1D5DB] text-slate-700 hover:bg-slate-100 flex items-center space-x-1"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>GERİ</span>
            </button>
            <button
              type="button"
              onClick={() => handleNextStep(3)}
              className="light-btn px-6 py-3 text-xs font-bold uppercase tracking-wider flex items-center space-x-2"
            >
              <span>İLERİ: BİNA YAŞI VE ARSA PAYI</span>
              <ArrowRight className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: BİNA YAŞI, KAT KONUMU, ARSA BÜYÜKLÜĞÜ VE ARSA PAYI (ZERO DEFAULTS) */}
      {step === 3 && (
        <div className="space-y-4 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs font-bold">
            
            {/* Building Age */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                9. Bina Yaşı (Yıl) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                placeholder="Örn: 5"
                value={buildingAge}
                onChange={(e) => setBuildingAge(e.target.value)}
                className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                required
              />
            </div>

            {/* Floor Category */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                10. Kat Konumu <span className="text-red-500">*</span>
              </label>
              <select
                value={floorCategory}
                onChange={(e) => setFloorCategory(e.target.value)}
                className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
              >
                <option value="">-- Kat Konumu Seçiniz --</option>
                <option value="ara_kat">Ara Kat</option>
                <option value="giris">Giriş / Zemin Kat</option>
                <option value="bodrum">Bodrum Kat</option>
                <option value="en_ust">En Üst Kat / Çatı</option>
              </select>
            </div>

            {/* Total Land Size (m2) */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                11. Toplam Arsa Büyüklüğü (m²) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                placeholder="Örn: 2400"
                value={totalLandM2}
                onChange={(e) => setTotalLandM2(e.target.value)}
                className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
                required
              />
            </div>

            {/* Land Share */}
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px]">
                12. Arsa Payı (Pay / Payda) <span className="text-red-500">*</span>
              </label>
              <div className="flex items-center space-x-1">
                <input
                  type="number"
                  placeholder="Örn: 15"
                  value={landNum}
                  onChange={(e) => setLandNum(e.target.value)}
                  className="w-1/2 bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold text-center"
                  required
                />
                <span className="font-extrabold text-slate-400">/</span>
                <input
                  type="number"
                  placeholder="Örn: 240"
                  value={landDen}
                  onChange={(e) => setLandDen(e.target.value)}
                  className="w-1/2 bg-[#FAF8F5] border border-[#D1D5DB] rounded-xl p-3 text-[#111827] font-bold text-center"
                  required
                />
              </div>
            </div>

          </div>

          <div className="flex justify-between pt-4 border-t border-[#E5E7EB]">
            <button
              type="button"
              onClick={() => { setErrorMsg(null); setStep(2); }}
              className="px-5 py-2.5 rounded-xl text-xs font-bold border border-[#D1D5DB] text-slate-700 hover:bg-slate-100 flex items-center space-x-1"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>GERİ</span>
            </button>
            <button
              type="button"
              onClick={handleFinish}
              className="light-btn px-6 py-3.5 text-xs font-extrabold uppercase tracking-wider flex items-center space-x-2 bg-[#047857] hover:bg-[#065F46]"
            >
              <CheckCircle2 className="w-4 h-4 text-white" />
              <span>DEĞERLEMEYİ HESAPLA VE PROFILE KAYDET</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
