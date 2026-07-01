from spark.bronze_stream import BronzeStreamConfig, DEFAULT_TOPICS, build_parser


def test_default_topics_match_phase_two_events():
    assert DEFAULT_TOPICS.split(",") == [
        "customers",
        "products",
        "orders",
        "payments",
        "clicks",
        "inventory",
    ]


def test_bronze_config_defaults_to_available_now():
    config = BronzeStreamConfig()

    assert config.trigger_available_now is True
    assert config.bronze_path == "data/bronze/events"
    assert config.quarantine_path == "data/bronze/quarantine/events"
    assert config.checkpoint_path == "data/bronze/_checkpoints/events"


def test_cli_can_switch_to_continuous_mode():
    args = build_parser().parse_args(["--continuous", "--processing-time", "10 seconds"])

    assert args.continuous is True
    assert args.processing_time == "10 seconds"
