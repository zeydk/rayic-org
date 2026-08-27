import os
import sys
import pytest

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.input_parser import parse_ad_text
from services.valuation_engine import calculate_valuation
from services.urban_transformation import simulate_urban_transformation
from services.financial_engine import calculate_financials
from services.spatial_service import analyze_spatial_data
from services.pdf_report import generate_checkup_pdf

def test_input_parser():
    sample_ad = "Kadıköy Caddebostan sahil tarafında satılık 12.500.000 TL net 95 m2 brüt 115m2 3+1 5 yaşında 3. kat arsa payı 15/240"
    res = parse_ad_text(sample_ad)
    
    assert res.price == 12500000.0
    assert res.net_m2 == 95.0
    assert res.gross_m2 == 115.0
    assert res.building_age == 5
    assert res.room_count == "3+1"
    assert res.land_share_num == 15.0
    assert res.land_share_den == 240.0
    assert res.district == "Kadıköy"
    assert res.neighborhood == "Caddebostan"
    assert len(res.missing_fields) == 0

def test_valuation_engine():
    res = calculate_valuation(
        price_advertised=10_000_000.0,
        net_m2=100.0,
        building_age=2,
        floor_category="ara_kat",
        district="Kadıköy",
        neighborhood="Caddebostan"
    )
    
    assert res.estimated_total_price > 14_000_000
    assert res.deviation_percent < -10.0
    assert res.deal_status == "firsat"

def test_urban_transformation():
    res = simulate_urban_transformation(
        advertised_price=12_000_000.0,
        current_net_m2=100.0,
        land_num=20.0,
        land_den=300.0,
        contractor_share_ratio=0.40,
        district="Kadıköy",
        neighborhood="Caddebostan"
    )
    
    # Arsa payı: (20/300) x 2400 (varsayılan toplam arsa) = 160 m²
    assert res.land_share_m2 == 160.0
    # Kullanıcının verdiği müteahhit oranı geçerli aralıkta -> aynen kullanılır
    assert res.contractor_share_percent == 40.0
    # Yeni daire = arsa payı x (1 - müteahhit oranı) x 1.15 = 160 x 0.6 x 1.15
    assert res.new_flat_net_m2 == 110.4
    assert res.estimated_new_building_price == 12_000_000.0 * 1.65
    assert res.value_appreciation_percent > 0.0


def test_urban_transformation_mahalle_orani():
    """Oran verilmezse mahalle haritasından gelmeli (Caddebostan = %42)."""
    res = simulate_urban_transformation(
        advertised_price=12_000_000.0,
        current_net_m2=100.0,
        land_num=20.0,
        land_den=300.0,
        contractor_share_ratio=None,
        district="Kadıköy",
        neighborhood="Caddebostan"
    )
    assert res.contractor_share_percent == 42.0
    assert res.new_flat_net_m2 == 106.7


def test_urban_transformation_taban_sinir():
    """Arsa payı çok küçükse yeni daire 45 m² tabanına sabitlenir."""
    res = simulate_urban_transformation(
        advertised_price=5_000_000.0,
        current_net_m2=60.0,
        total_land_m2=300.0,
        land_num=5.0,
        land_den=100.0,
        contractor_share_ratio=0.50
    )
    assert res.land_share_m2 == 15.0
    assert res.new_flat_net_m2 == 45.0

def test_spatial_analysis():
    res = analyze_spatial_data(
        lat=40.9675,
        lng=29.0652,
        district="Kadıköy",
        neighborhood="Caddebostan"
    )
    
    assert len(res.pois_within_1km) > 0
    assert res.ground_risk_class != ""
    assert res.pga_earthquake_risk_score > 0.0

def test_pdf_generation():
    ad_data = {
        "price": 12500000.0,
        "net_m2": 95.0,
        "gross_m2": 115.0,
        "building_age": 10,
        "floor": "3. Kat",
        "district": "Kadıköy",
        "neighborhood": "Caddebostan",
        "room_count": "3+1"
    }
    val_res = calculate_valuation(
        price_advertised=12500000.0,
        net_m2=95.0,
        building_age=10,
        floor_category="ara_kat",
        district="Kadıköy",
        neighborhood="Caddebostan"
    )
    urban_res = simulate_urban_transformation(
        advertised_price=12500000.0,
        current_net_m2=95.0,
        land_num=15.0,
        land_den=240.0,
        contractor_share_ratio=0.42,
        district="Kadıköy",
        neighborhood="Caddebostan"
    )
    fin_res = calculate_financials(
        advertised_price=12500000.0,
        net_m2=95.0,
        district="Kadıköy",
        building_age=10
    )
    spatial_res = analyze_spatial_data(
        lat=40.9675,
        lng=29.0652,
        district="Kadıköy",
        neighborhood="Caddebostan"
    )

    pdf_bytes = generate_checkup_pdf(
        ad_data=ad_data,
        valuation=val_res.dict(),
        spatial=spatial_res.dict(),
        urban=urban_res.dict(),
        financial=fin_res.dict()
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
