CREATE TABLE raw_orderbook(
    id INTEGER PRIMARY KEY,
    pair VARCHAR(20) NOT NULL,
    price REAL NOT NULL,
    volume REAL NOT NULL,
    is_ask BOOLEAN NOT NULL,
    order_epoch INTEGER NOT NULL,
    snapshot_epoch REAL NOT NULL
);