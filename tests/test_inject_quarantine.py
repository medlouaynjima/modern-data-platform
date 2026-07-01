from __future__ import annotations

from producer.inject_quarantine import invalid_events


def test_invalid_events_are_marked_invalid_by_validator() -> None:
    from contracts.validator import validate_batch, validate_event

    records = invalid_events()
    assert len(records) >= 5

    non_order_records = [(topic, event) for topic, _key, event, _reason in records if topic != "orders"]
    for topic, event in non_order_records:
        assert not validate_event(topic, event).valid

    order_events = [event for topic, _key, event, _reason in records if topic == "orders"]
    order_results = validate_batch("orders", order_events)
    assert not all(result.valid for result in order_results)
