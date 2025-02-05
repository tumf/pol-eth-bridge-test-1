from web3 import Web3
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Network RPC endpoints
ETH_RPC_URL = os.getenv(
    "ETH_RPC_URL", "https://mainnet.infura.io/v3/YOUR-INFURA-PROJECT-ID"
)
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")

# Contract addresses
CHILD_TOKEN_ADDRESS = os.getenv("CHILD_TOKEN_ADDRESS")  # Polygon token address
ROOT_CHAIN_MANAGER_ADDRESS = (
    "0x86E4Dc95c7FBdBf52e33D563BbDB00823894c287"  # Fixed address on Ethereum
)

# Initialize Web3 instances
w3_eth = Web3(Web3.HTTPProvider(ETH_RPC_URL))
w3_polygon = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))

# Load wallet
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("Private key not found in environment variables")

account = w3_eth.eth.account.from_key(PRIVATE_KEY)
my_address = account.address
print(f"Using account: {my_address}")

# Contract ABIs
child_token_abi = [
    {
        "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

root_chain_manager_abi = [
    {
        "inputs": [{"internalType": "bytes", "name": "data", "type": "bytes"}],
        "name": "exit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def withdraw_from_polygon(amount_in_wei):
    """Step 1: Withdraw (burn) tokens on Polygon"""
    child_token = w3_polygon.eth.contract(
        address=Web3.to_checksum_address(CHILD_TOKEN_ADDRESS), abi=child_token_abi
    )

    # Build withdraw transaction
    nonce = w3_polygon.eth.get_transaction_count(my_address)
    txn = child_token.functions.withdraw(amount_in_wei).build_transaction(
        {
            "from": my_address,
            "chainId": 137,  # Polygon mainnet
            "nonce": nonce,
        }
    )

    # Estimate gas and set gas price
    gas_limit = w3_polygon.eth.estimate_gas(txn)
    txn["gas"] = int(gas_limit * 1.2)  # Add 20% margin
    txn["gasPrice"] = w3_polygon.eth.gas_price

    # Sign and send transaction
    signed_txn = w3_polygon.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3_polygon.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Withdraw TX sent: {tx_hash.hex()}")

    # Wait for transaction confirmation
    receipt = w3_polygon.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.status != 1:
        raise Exception("Withdraw transaction failed on Polygon side")
    print(f"Withdraw confirmed in block {receipt.blockNumber}")
    return tx_hash.hex()


def wait_for_checkpoint(burn_tx_hash):
    """Step 2: Wait for checkpoint and get exit payload"""
    print("Waiting for checkpoint (this may take 30+ minutes)...")
    time.sleep(1800)  # Wait 30 minutes for checkpoint

    # Get exit payload from Polygon API
    transfer_event_sig = Web3.keccak(text="Transfer(address,address,uint256)").hex()
    url = f"https://apis.matic.network/api/v1/matic/exit-payload/{burn_tx_hash}?eventSignature={transfer_event_sig}"

    response = requests.get(url)
    if response.status_code != 200 or "result" not in response.json():
        raise Exception(
            "Failed to retrieve exit payload. Check if checkpoint is completed."
        )

    return response.json()["result"]


def exit_to_ethereum(exit_payload):
    """Step 3: Submit exit proof to Ethereum"""
    root_chain_manager = w3_eth.eth.contract(
        address=Web3.to_checksum_address(ROOT_CHAIN_MANAGER_ADDRESS),
        abi=root_chain_manager_abi,
    )

    # Build exit transaction
    eth_nonce = w3_eth.eth.get_transaction_count(my_address)
    exit_txn = root_chain_manager.functions.exit(exit_payload).build_transaction(
        {
            "from": my_address,
            "chainId": 1,  # Ethereum mainnet
            "nonce": eth_nonce,
        }
    )

    # Estimate gas and set EIP-1559 fees
    gas_limit = w3_eth.eth.estimate_gas(exit_txn)
    exit_txn["gas"] = int(gas_limit * 1.1)

    base_fee = w3_eth.eth.get_block("latest")["baseFeePerGas"]
    priority_fee = w3_eth.eth.max_priority_fee
    max_fee = base_fee * 2 + priority_fee
    exit_txn["maxPriorityFeePerGas"] = priority_fee
    exit_txn["maxFeePerGas"] = max_fee

    # Sign and send transaction
    signed_exit_txn = w3_eth.eth.account.sign_transaction(
        exit_txn, private_key=PRIVATE_KEY
    )
    exit_tx_hash = w3_eth.eth.send_raw_transaction(signed_exit_txn.rawTransaction)
    print(f"Exit TX sent: {exit_tx_hash.hex()}")

    # Wait for transaction confirmation
    exit_receipt = w3_eth.eth.wait_for_transaction_receipt(exit_tx_hash, timeout=300)
    if exit_receipt.status != 1:
        raise Exception("Exit transaction failed on Ethereum side")
    print("Exit transaction confirmed. Tokens should be unlocked to your address.")


def main():
    # Amount of tokens to bridge (example: 100 tokens with 18 decimals)
    amount = 100
    amount_in_wei = amount * (10**18)

    try:
        # Step 1: Withdraw on Polygon
        burn_tx_hash = withdraw_from_polygon(amount_in_wei)

        # Step 2: Wait for checkpoint and get proof
        exit_payload = wait_for_checkpoint(burn_tx_hash)

        # Step 3: Exit on Ethereum
        exit_to_ethereum(exit_payload)

        print("Bridge process completed successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
