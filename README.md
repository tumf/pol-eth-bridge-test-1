# Polygon to Ethereum Bridge Test part 1

This project implements a bridge to transfer tokens from Polygon (Layer 2) back to Ethereum (Layer 1) using the Polygon PoS Bridge mechanism.

## Features

- Withdraw (burn) tokens on Polygon network
- Wait for checkpoint completion
- Submit proof to unlock tokens on Ethereum

## Prerequisites

- Python 3.13 or higher
- Ethereum wallet with private key
- Infura account (or other Ethereum RPC provider)
- Sufficient tokens on Polygon network
- Sufficient MATIC for gas fees on Polygon
- Sufficient ETH for gas fees on Ethereum

## Setup

1. Clone the repository

2. Install dependencies using uv:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

3. Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

4. Set the following environment variables in `.env`:
- `ETH_RPC_URL`: Your Ethereum RPC endpoint
- `POLYGON_RPC_URL`: Polygon RPC endpoint
- `PRIVATE_KEY`: Your wallet's private key (without 0x prefix)
- `CHILD_TOKEN_ADDRESS`: Token contract address on Polygon

## Dependencies

- python-dotenv >= 1.0.1
- requests >= 2.32.3
- web3 >= 7.8.0

## Usage

Run the bridge script:

```bash
python bridge_to_ethereum.py
```

The script will:
1. Withdraw tokens on Polygon
2. Wait for checkpoint (approximately 30 minutes)
3. Submit proof to unlock tokens on Ethereum

## Important Notes

- The bridge process takes approximately 30+ minutes due to checkpoint requirements
- Ensure sufficient gas fees on both networks
- Keep your private key secure and never share it
- Test with small amounts first

## Network Addresses

- Root Chain Manager (Ethereum): `0x86E4Dc95c7FBdBf52e33D563BbDB00823894c287`
- Child Token (Polygon): Set in environment variables
