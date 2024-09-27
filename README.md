# Scalable and Fault-Tolerant Order Processing System

This project demonstrates how to build a scalable and fault-tolerant order processing system using **FastAPI**,
**PostgreSQL**, **RabbitMQ**, **Docker**, and **Nginx** to handle spikes and high traffic.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Usage](#usage)
5. [Performance](#performance)

## Overview

This system allows users to place orders and retrieve their status asynchronously. It uses:

- **FastAPI** for the API
- **PostgreSQL** for order storage
- **RabbitMQ** for queuing tasks
- **Consumer Service** for processing orders
- **Nginx** as a reverse proxy and load balancer

## Architecture

The system consists of the following components:

1. **Client**: Makes HTTP requests to place orders and retrieve their status.
2. **API (FastAPI)**: Handles client requests, stores order data in PostgreSQL, and sends order processing tasks to
   RabbitMQ.
3. **Database (PostgreSQL)**: Stores order details and statuses.
4. **Message Queue (RabbitMQ)**: Queues order processing tasks for asynchronous handling.
5. **Consumer**: Listens to RabbitMQ, processes the orders, and updates their status in the database.
6. **Nginx**: Distributes incoming HTTP requests across multiple API instances.

## Getting Started

### Prerequisites

Ensure you have:

- **Docker** and **Docker Compose** installed.

### Clone the Repository

```bash
git clone https://github.com/punitarani/message-queue.git
cd message-queue
```

### Start the System

Run all services with Docker Compose:

```bash
docker-compose up --build
```

### Access the Services

- **API**: `http://localhost:3000` (FastAPI)
- **Nginx**: `http://localhost:80` (Entry point for all API traffic)
- **RabbitMQ Management UI**: `http://localhost:15672` (Default credentials: `guest` / `guest`)

## Usage

### Place an Order

Send a `POST` request to place an order:

```bash
curl -X POST http://localhost:80/order/place
```

This will create a new order and queue it for processing.

### Check Order Status

Send a `GET` request with the `order_id` to check the status:

```bash
curl -X GET http://localhost:80/order/get/{order_id}
```

Replace `{order_id}` with the ID returned when the order was created.

## Performance

- The system can handle over **1600 requests per second** on modest hardware.
- **Median latency** is less than **100ms**.
- **99th percentile latency** is less than **1s**.

The performance depends largely on the database connection pool settings and RabbitMQ message processing.

---

Punit Arani
