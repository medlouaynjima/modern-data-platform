# Kafka Topics

| Topic | Entity | Producer Phase | Notes |
| --- | --- | --- | --- |
| `customers` | Customer profile events | Phase 2 | Slowly changing customer attributes |
| `products` | Product catalog events | Phase 2 | Category, margin, and pricing inputs |
| `orders` | Order placement events | Phase 2 | Main sales fact source |
| `payments` | Payment authorization events | Phase 2 | Fraud and revenue validation input |
| `clicks` | Clickstream events | Phase 2 | Product analytics and recommendations |
| `inventory` | Stock movement events | Phase 2 | Availability and supply signals |
