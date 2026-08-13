"use client";

import React, { useState } from "react";
import { BookOpen, CheckCircle2, ShieldAlert, FileText, Landmark, Scale, DollarSign, AlertTriangle } from "lucide-react";

export default function GuidesView() {
  const [activeGuideTab, setActiveGuideTab] = useState<"buying" | "selling" | "dictionary">("buying");

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* Main Header */}
      <div className="light-card p-6 bg-white border border-[#E5E7EB] space-y-3">
        <div className="flex items-center space-x-2 text-xs font-bold text-[#111827]">
          <BookOpen className="w-4 h-4 text-[#111827]" />
          <span>GAYRİMENKUL &amp; TAPU REHBERİ</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[#111827] font-display">
          Uzman Gayrimenkul ve Tapu Rehberi
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 max-w-3xl font-medium">
          Ev alım ve satım süreçlerinde hukuki riskleri sıfırlayan, vergi muafiyetlerini açıklayan ve tapu devrini güvenceye alan pratik bilgiler.
        </p>

        {/* Guide Sub-Navigation Tabs */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-[#E5E7EB]">
          <button
            onClick={() => setActiveGuideTab("buying")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
              activeGuideTab === "buying"
                ? "bg-[#111827] text-white border-[#111827] shadow-sm"
                : "bg-[#FAF8F5] text-[#111827] border-[#E5E7EB] hover:border-[#111827]"
            }`}
          >
            🔑 Ev Alırken Bilinmesi Gerekenler
          </button>

          <button
            onClick={() => setActiveGuideTab("selling")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
              activeGuideTab === "selling"
                ? "bg-[#111827] text-white border-[#111827] shadow-sm"
                : "bg-[#FAF8F5] text-[#111827] border-[#E5E7EB] hover:border-[#111827]"
            }`}
          >
            🏠 Ev Satarken Bilinmesi Gerekenler
          </button>

          <button
            onClick={() => setActiveGuideTab("dictionary")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
              activeGuideTab === "dictionary"
                ? "bg-[#111827] text-white border-[#111827] shadow-sm"
                : "bg-[#FAF8F5] text-[#111827] border-[#E5E7EB] hover:border-[#111827]"
            }`}
          >
            📖 Gayrimenkul &amp; Tapu Terimleri Sözlüğü
          </button>
        </div>
      </div>

      {/* SUB-MENU 1: EV ALIRKEN BİLİNMESİ GEREKENLER (Distinct & Practical) */}
      {activeGuideTab === "buying" && (
        <div className="space-y-4 animate-fadeIn">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Guide 1.1 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">01. HUKUKİ GÜVENCE</span>
                <Landmark className="w-4 h-4 text-[#111827]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                Kat Mülkiyeti mi, Kat İrtifakı mı? (İskan Riski)
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Satın alacağınız evin tapusunda **"Kat Mülkiyeti"** yazması, binanın belediyeden onaylı mimari projesine uygun tamamlandığını ve **Yapı Kullanma İzin Belgesi (İskan)** alındığını gösterir. Kat irtifaklı evlerde iskan alınmamışsa, bina şantiye elektriği/suyu tarifesinden faturalandırılabilir ve bankalar kredi limitini düşürebilir.
              </p>
            </div>

            {/* Guide 1.2 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">02. GÜVENLİ ÖDEME</span>
                <ShieldAlert className="w-4 h-4 text-[#047857]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                Tapu Takas Sistemi ve Sahte Para Güvencesi
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Tapu devrinde nakit para taşıma veya dolandırıcılık riskini önlemek için Tapu ve Kadastro Genel Müdürlüğü'nün **TKGM Tapu Takas (Takasbank)** sistemini kullanın. Satış bedeli emanet hesaba alınır; tapu imzası atıldığı anda para otomatik olarak satıcının hesabına aktarılır.
              </p>
            </div>

            {/* Guide 1.3 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">03. PROJE UYGUNLUĞU</span>
                <FileText className="w-4 h-4 text-[#111827]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                Belediye Mimari Projesi ile Daire Kontrolü
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Fiziksel gezdiğiniz daire ile belediyedeki onaylı proje örtüşüyor mu? Sonradan kaçak olarak birleştirilen çatı araları, balkonu odaya katma veya ortak alandan sığınak/depo dahil etme durumları belediye yıkım kararlarına veya cezalara sebep olabilir.
              </p>
            </div>

            {/* Guide 1.4 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">04. BORÇ VE ŞERH KONTROLÜ</span>
                <Scale className="w-4 h-4 text-[#C2410C]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                İpotek, Haciz ve Geçmiş Emlak Vergisi
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Tapu kütüğü üzerinde kamu haczi, banka ipoteği veya aile konutu şerhi olup olmadığını e-Devlet veya tapu müdürlüğü üzerinden inceleyin. Ayrıca satıcının geçmiş emlak vergisi ve bina ortak gider aidat borcu bulunmadığına dair belge isteyin.
              </p>
            </div>

          </div>

          <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] text-xs font-bold text-[#111827] flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" />
            <span>
              <strong>ALICI İPUCU:</strong> Evde kiracı bulunuyorsa, satın almadan önce kira sözleşmesi şartlarını inceleyin. Kendiniz oturacaksanız, tapu devrinden itibaren 1 ay içinde kiracıya noterden ihbarname çekmeniz kanuni zorunluluktur.
            </span>
          </div>

        </div>
      )}

      {/* SUB-MENU 2: EV SATARKEN BİLİNMESİ GEREKENLER (Distinct & Practical) */}
      {activeGuideTab === "selling" && (
        <div className="space-y-4 animate-fadeIn">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Guide 2.1 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">01. VERGİ MUAFİYETİ</span>
                <DollarSign className="w-4 h-4 text-[#047857]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                Değer Artış Kazancı Vergisi ve 5 Yıl Kuralı
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Evinizi satın aldığınız (iktisap) tarihten itibaren **5 tam yıl (60 ay)** tamamlanmadan satıyorsanız, alış ve satış bedeli arasındaki kâr üzerinden Gelir Vergisi (Değer Artış Kazancı) ödemeniz gerekir. 5 yılı dolduran ev satışlarında ise bu vergi tamamen sıfırlanır.
              </p>
            </div>

            {/* Guide 2.2 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">02. FİYATLAMA STRATEJİSİ</span>
                <Landmark className="w-4 h-4 text-[#111827]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                Doğru İlan Fiyatlaması ve İlanın "Yankılanma" Riski
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Evinizi piyasa değerinin %15-20 üzerinde ilana çıkarmak, ilanın portallarda aylarca kalmasına ve alıcılar gözünde "sorunlu ev" algısı oluşmasına sebep olur. Gerçek piyasa ekspertiz değerinin %3-5 üzerinde pazarlık marjı koyarak yayına çıkmak en hızlı satışı sağlar.
              </p>
            </div>

            {/* Guide 2.3 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">03. BELEDİYE BELGELERİ</span>
                <FileText className="w-4 h-4 text-[#111827]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                Emlak Rayiç Değer Belgesi Hazırlığı
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Tapuda satış randevusu alabilmek için konutun bağlı olduğu ilçe belediyesinden **"Emlak Vergisi Bildirim Değeri (Rayiç Belgesi)"** alınmalıdır. Tapu harcı, beyan edilen satış bedeli ile belediye rayiç değerinden yüksek olanı üzerinden hesaplanır.
              </p>
            </div>

            {/* Guide 2.4 */}
            <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="light-badge text-[9px]">04. SÖZLEŞME VE KAPARO</span>
                <Scale className="w-4 h-4 text-[#C2410C]" />
              </div>
              <h3 className="text-base font-extrabold text-[#111827]">
                Kaparo Alımı ve Ön Satış Protokolü
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Alıcıdan kaparo alırken mutlaka yazılı bir "Satış Vaadi ve Kaparo Protokolü" imzalayın. Kaparoyu elden almak yerine bankadan açıklamasına *"Gayrimenkul Satış Kaparo Bedeli"* yazdırarak alın. Alıcının vazgeçmesi halinde bağlanma parası kurallarını belirleyin.
              </p>
            </div>

          </div>

          <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] text-xs font-bold text-[#111827] flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" />
            <span>
              <strong>SATICI İPUCU:</strong> Tapu devir günü satış bedelini hesabınızda görmeden veya Tapu Takas sistemi onay vermeden tapu kütüğüne imza atmayın.
            </span>
          </div>

        </div>
      )}

      {/* SUB-MENU 3: GAYRİMENKUL & TAPU SÖZLÜĞÜ (Clear & Concrete) */}
      {activeGuideTab === "dictionary" && (
        <div className="light-card p-6 bg-white border border-[#E5E7EB] space-y-4 animate-fadeIn">
          <h3 className="text-base font-extrabold text-[#111827] font-display">
            Gayrimenkul ve Tapu Terimleri Sözlüğü
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-bold">
            
            <div className="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-1">
              <span className="text-[#111827] font-mono text-sm block">Kat Mülkiyeti</span>
              <p className="text-slate-600 font-medium text-[11px]">
                İnşaatı tamamlanmış ve belediyeden yapı kullanma izin belgesi (iskan) alınmış bağımsız bölümlerin resmi tapu senedidir.
              </p>
            </div>

            <div className="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-1">
              <span className="text-[#111827] font-mono text-sm block">Kat İrtifakı</span>
              <p className="text-slate-600 font-medium text-[11px]">
                Henüz tamamlanmamış veya iskanı alınmamış binalarda projedeki dairelerin arsa üzerindeki pay hakkını gösteren geçici tapu türüdür.
              </p>
            </div>

            <div className="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-1">
              <span className="text-[#111827] font-mono text-sm block">Arsa Payı (Pay / Payda)</span>
              <p className="text-slate-600 font-medium text-[11px]">
                Binanın oturduğu toplam arsa parselinde daireye düşen m² pay oranıdır (Örn: 2400 m² arsa üzerinde 15/240 pay = 150 m² arsa hakkı).
              </p>
            </div>

            <div className="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-1">
              <span className="text-[#111827] font-mono text-sm block">İskan (Yapı Kullanma İzin Belgesi)</span>
              <p className="text-slate-600 font-medium text-[11px]">
                Binanın sığınak, yangın, mimari ve statik projesine uygun inşa edildiğini onaylayan belediye izin belgesidir.
              </p>
            </div>

            <div className="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-1">
              <span className="text-[#111827] font-mono text-sm block">Şerefiye</span>
              <p className="text-slate-600 font-medium text-[11px]">
                Aynı binadaki dairelerin kat yüksekliği, cephe yönü (güney/kuzey), manzara ve ışık alma durumuna göre oluşan değer farkıdır.
              </p>
            </div>

            <div className="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-1">
              <span className="text-[#111827] font-mono text-sm block">Cins Tashihi</span>
              <p className="text-slate-600 font-medium text-[11px]">
                Tapu kütüğünde "arsa" olarak görünen mülkün cinsinin resmi olarak "kargir bina ve dairesi" olarak dönüştürülmesi işlemidir.
              </p>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
