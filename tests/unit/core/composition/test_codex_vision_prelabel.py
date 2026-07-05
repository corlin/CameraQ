from tests.fixtures.composition import codex_vision_prelabel


def test_unreviewed_contact_sheet_index_stays_pending():
    decision, confidence = codex_vision_prelabel.classify_index(
        "horizontal-photo-positive", 99
    )

    assert decision == "pending"
    assert confidence == "0.00"
