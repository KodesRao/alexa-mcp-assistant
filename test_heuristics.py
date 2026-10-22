from heuristics import analyze_listing, find_disguised_brands

def test_disguised_brand():
    assert "nike" in find_disguised_brands("N.i.k.e Air Max shoes")
    assert "nike" in find_disguised_brands("N1ke running shoes")
    assert "adidas" in find_disguised_brands("a d i d a s Yeezy")

def test_plain_brand_not_flagged():
    assert find_disguised_brands("Nike Air Max 90 original") == []

def test_counterfeit_wording():
    r = analyze_listing("Premium 1:1 AAA mirror quality sneakers")
    assert r["verdict"] in ("CAUTION", "HIGH_RISK") and r["reasons"]

def test_price_signal():
    r = analyze_listing("Nike Air Max 90", listed_price=90, official_price=429)
    assert r["price_ratio"] == 0.21 and r["score"] >= 45

def test_clean_listing():
    r = analyze_listing("Nike Air Max 90 men shoes", listed_price=410, official_price=429)
    assert r["verdict"] == "LOOKS_OK"

def test_product_line_without_brand():
    r = analyze_listing("Air Jordan 1 high top")
    assert any("never names" in x for x in r["reasons"])

def test_worst_case():
    r = analyze_listing("N1ke Air Max 1:1 OEM", listed_price=80, official_price=429)
    assert r["verdict"] == "HIGH_RISK"

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
