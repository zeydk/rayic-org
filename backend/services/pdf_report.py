import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

def generate_checkup_pdf(
    ad_data: dict,
    valuation: dict,
    spatial: dict,
    urban: dict,
    financial: dict
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        'DocHeader',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        alignment=0
    )
    
    subheader_style = ParagraphStyle(
        'DocSubHeader',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#64748B')
    )

    section_title = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )

    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.white,
        alignment=1
    )

    story = []
    
    # Header Banner
    story.append(Paragraph("rayic.org | GAYRİMENKUL CHECK-UP RAPORU", header_style))
    story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Rapor No: RYC-{int(datetime.now().timestamp())}", subheader_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3B82F6'), spaceAfter=10))

    # 1. Listing Overview Table
    story.append(Paragraph("1. MÜLK VE İLAN ÖZET BİLGİLERİ", section_title))
    
    price_val = ad_data.get('price') or 0.0
    net_m2_val = ad_data.get('net_m2') or 0.0
    gross_m2_val = ad_data.get('gross_m2') or (net_m2_val * 1.18)
    
    price_formatted = f"{price_val:,.0f} TL".replace(",", ".")
    net_m2_str = f"{net_m2_val:.0f} m²"
    gross_m2_str = f"{gross_m2_val:.0f} m²"
    building_age = f"{ad_data.get('building_age', 5)} Yıl"
    floor = str(ad_data.get('floor_name') or ad_data.get('floor') or 'Ara Kat')
    location_str = f"{ad_data.get('district', 'Kadıköy')} / {ad_data.get('neighborhood', 'Caddebostan')}"

    overview_data = [
        [Paragraph("Lokasyon / Mahalle", cell_bold), Paragraph(location_str, cell_normal), Paragraph("İlan Fiyatı", cell_bold), Paragraph(price_formatted, cell_bold)],
        [Paragraph("Net / Brüt Alan", cell_bold), Paragraph(f"{net_m2_str} / {gross_m2_str}", cell_normal), Paragraph("Bina Yaşı", cell_bold), Paragraph(building_age, cell_normal)],
        [Paragraph("Kat Bilgisi", cell_bold), Paragraph(floor, cell_normal), Paragraph("Oda Sayısı", cell_bold), Paragraph(str(ad_data.get('room_count', '3+1')), cell_normal)],
    ]

    t_overview = Table(overview_data, colWidths=[3.5*cm, 5.0*cm, 3.5*cm, 5.0*cm])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_overview)
    story.append(Spacer(1, 0.4*cm))

    # 2. Valuation & Inflation Score (AVM)
    story.append(Paragraph("2. OTOMATİK DEĞERLEME (AVM) VE ŞİŞKİNLİK SKORU", section_title))
    
    est_price = valuation.get('estimated_total_price') or 0.0
    est_price_fmt = f"{est_price:,.0f} TL".replace(",", ".")
    dev_percent = valuation.get('deviation_percent') or 0.0
    dev_sign = "+" if dev_percent > 0 else ""
    dev_str = f"{dev_sign}{dev_percent:.1f}%"
    
    badge_bg = colors.HexColor(valuation.get('status_color', '#3B82F6'))
    status_lbl = valuation.get('status_label', 'Makul Piyasa Değeri')
    
    badge_table = Table([[Paragraph(status_lbl, badge_style)]], colWidths=[17.0*cm])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), badge_bg),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 0.3*cm))

    base_m2_val = valuation.get('base_m2_price') or 0.0

    val_data = [
        [Paragraph("Metrik", cell_bold), Paragraph("Değer", cell_bold), Paragraph("Açıklama", cell_bold)],
        [Paragraph("Mahalle m² Rayiç Fiyatı", cell_normal), Paragraph(f"{base_m2_val:,.0f} TL/m²", cell_normal), Paragraph("Cold-start bölge ortalama birim fiyatı", cell_normal)],
        [Paragraph("Tahmini Piyasa Değeri", cell_bold), Paragraph(est_price_fmt, cell_bold), Paragraph("Şerefiye, yaş ve kat amortismanı uygulanmış değer", cell_normal)],
        [Paragraph("Fiyat Sapma Oranı", cell_bold), Paragraph(dev_str, cell_bold), Paragraph("İlan fiyatının tahmini değere göre oranı", cell_normal)],
    ]
    t_val = Table(val_data, colWidths=[5.0*cm, 4.5*cm, 7.5*cm])
    t_val.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_val)
    story.append(Spacer(1, 0.4*cm))

    # 3. Spatial & POI Risk Katmanı
    story.append(Paragraph("3. MEKÂNSAL VE ZEMİN RİSK KATMANI (1 KM POI ANALİZİ)", section_title))
    
    ground_risk = spatial.get('ground_risk_class', 'Z2 (Orta Güvenli Zemin)')
    pga_score = spatial.get('pga_earthquake_risk_score') or 0.28
    poi_summary = spatial.get('poi_summary') or {}

    spatial_data = [
        [Paragraph("Zemin Risk Sınıfı", cell_bold), Paragraph(ground_risk, cell_normal)],
        [Paragraph("Deprem İvme Değeri (PGA)", cell_bold), Paragraph(f"{pga_score} g", cell_normal)],
        [Paragraph("1 km Yarıçap Rayic POI", cell_bold), Paragraph(f"Metro: {poi_summary.get('metro',0)} | Metrobüs: {poi_summary.get('metrobus',0)} | Hastane: {poi_summary.get('hospital',0)} | Dönüşüm Şantiyesi: {poi_summary.get('transformation',0)}", cell_normal)]
    ]
    t_spatial = Table(spatial_data, colWidths=[5.5*cm, 11.5*cm])
    t_spatial.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_spatial)

    # PAGE BREAK
    story.append(PageBreak())

    # PAGE 2
    story.append(Paragraph("rayic.org | CHECK-UP RAPORU (SAYFA 2 / 2)", subheader_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94A3B8'), spaceAfter=10))

    # 4. Kentsel Dönüşüm & Arsa Payı Simülatörü
    story.append(Paragraph("4. KENTSEL DÖNÜŞÜM VE ARSA PAYI SİMÜLATÖRÜ", section_title))
    
    new_m2_val = urban.get('estimated_new_net_m2') or 0.0
    new_m2_str = f"{new_m2_val:.0f} m²"
    contractor_ratio = urban.get('contractor_share_ratio') or 0.42
    contractor_pct = f"%{contractor_ratio*100:.0f}"
    land_sec_val = urban.get('land_security_ratio_percent') or 0.0
    land_sec = f"%{land_sec_val:.1f}"
    borrowing_val = urban.get('estimated_construction_borrowing_cost') or 0.0
    borrowing = f"{borrowing_val:,.0f} TL".replace(",", ".")
    new_val_num = urban.get('new_apartment_value') or 0.0
    new_val = f"{new_val_num:,.0f} TL".replace(",", ".")
    net_roi_val = urban.get('net_transformation_roi_tl') or 0.0
    net_roi = f"{net_roi_val:,.0f} TL".replace(",", ".")
    roi_pct_val = urban.get('roi_percent') or 0.0
    roi_pct = f"%{roi_pct_val:.1f}"

    urban_table_data = [
        [Paragraph("Metrik", cell_bold), Paragraph("Değer", cell_bold)],
        [Paragraph("Mevcut Net m² ──► Tahmini Yeni Net m²", cell_normal), Paragraph(f"{net_m2_val:.0f} m² ──► {new_m2_str} ({contractor_pct} müteahhit payı)", cell_normal)],
        [Paragraph("Arsa Güvence Oranı (%)", cell_bold), Paragraph(land_sec, cell_bold)],
        [Paragraph("Tahmini İnşaat Borçlanma Maliyeti", cell_normal), Paragraph(borrowing, cell_normal)],
        [Paragraph("Yenilenmiş Daire Rayiç Değeri", cell_normal), Paragraph(new_val, cell_normal)],
        [Paragraph("Dönüşüm Net ROI (Prim Sıçraması)", cell_bold), Paragraph(f"{net_roi} ({roi_pct} Net Kazanç)", cell_bold)],
    ]
    t_urban = Table(urban_table_data, colWidths=[7.0*cm, 10.0*cm])
    t_urban.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_urban)
    story.append(Spacer(1, 0.4*cm))

    # 5. Finansal Getiri & Amortisman
    story.append(Paragraph("5. FİNANSAL GETİRİ VE AMORTİSMAN MOTORU", section_title))
    
    monthly_rent_val = financial.get('estimated_monthly_rent') or 0.0
    monthly_rent = f"{monthly_rent_val:,.0f} TL/Ay".replace(",", ".")
    gross_yield_val = financial.get('gross_yield_percent') or 0.0
    gross_yield = f"%{gross_yield_val:.2f}"
    amort_years_val = financial.get('amortization_years') or 0.0
    amort_months_val = financial.get('amortization_months') or 0
    amort_years = f"{amort_years_val:.1f} Yıl ({amort_months_val} Ay)"
    rating = financial.get('investment_rating', 'Makul Piyasa Ortalaması')

    fin_table_data = [
        [Paragraph("Tahmini Aylık Kira Getirisi", cell_normal), Paragraph(monthly_rent, cell_bold)],
        [Paragraph("Yıllık Brüt Getiri Oranı (%)", cell_normal), Paragraph(gross_yield, cell_bold)],
        [Paragraph("Geri Dönüş (Amortisman) Süresi", cell_bold), Paragraph(amort_years, cell_bold)],
        [Paragraph("Yatırım Değerlendirmesi", cell_bold), Paragraph(rating, cell_normal)],
    ]
    t_fin = Table(fin_table_data, colWidths=[7.0*cm, 10.0*cm])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 0.8*cm))

    # Legal Disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B'),
        alignment=0
    )
    disclaimer_text = (
        "Yasal Uyarı: Bu Gayrimenkul Check-Up Raporu rayic.org algoritmik değerleme motoru tarafından "
        "kamuya açık makro endeksler ve cold-start verileri kullanılarak otomatik üretilmiştir. "
        "Yatırım tavsiyesi niteliğinde olmayıp resmi gayrimenkul değerleme raporu yerine geçmez."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
