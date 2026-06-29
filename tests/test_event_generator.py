from producer.config import TOPICS
from producer.generator import RetailEventGenerator
from producer.main import record_key, records_from_events


def test_generator_emits_all_phase_two_topics():
    generator = RetailEventGenerator(seed=7)

    events = generator.event_batch(events_per_topic=2)
    topics = [topic for topic, _ in events]

    assert len(events) == 12
    assert set(topics) == set(TOPICS)
    assert all(topics.count(topic) == 2 for topic in TOPICS)


def test_events_have_common_metadata():
    generator = RetailEventGenerator(seed=11)

    for topic in TOPICS:
        event = generator.event_for_topic(topic)

        assert event["event_id"]
        assert event["event_type"]
        assert event["timestamp"].endswith("Z")


def test_topic_record_keys_are_stable_business_keys():
    generator = RetailEventGenerator(seed=13)
    records = list(records_from_events(generator.event_batch(events_per_topic=1)))

    for topic, key, event in records:
        assert key == record_key(topic, event)
        assert key
