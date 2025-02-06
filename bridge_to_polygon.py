from web3 import Web3
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
ROOT_TOKEN_ADDRESS = os.getenv("ROOT_TOKEN_ADDRESS")  # Ethereum token address
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
root_token_abi = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

root_chain_manager_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "rootToken", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "depositFor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

def approve_token(amount_in_wei):
    """Step 1: Approve tokens for deposit"""
    root_token = w3_eth.eth.contract(
        address=Web3.to_checksum_address(ROOT_TOKEN_ADDRESS),
        abi=root_token_abi
    )

    # Build approve transaction
    nonce = w3_eth.eth.get_transaction_count(my_address)
    txn = root_token.functions.approve(
        ROOT_CHAIN_MANAGER_ADDRESS,
        amount_in_wei
    ).build_transaction({
        "from": my_address,
        "chainId": 1,  # Ethereum mainnet
        "nonce": nonce,
    })

    # Estimate gas and set EIP-1559 fees
    gas_limit = w3_eth.eth.estimate_gas(txn)
    txn["gas"] = int(gas_limit * 1.1)

    base_fee = w3_eth.eth.get_block("latest")["baseFeePerGas"]
    priority_fee = w3_eth.eth.max_priority_fee
    max_fee = base_fee * 2 + priority_fee
    txn["maxPriorityFeePerGas"] = priority_fee
    txn["maxFeePerGas"] = max_fee

    # Sign and send transaction
    signed_txn = w3_eth.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3_eth.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Approve TX sent: {tx_hash.hex()}")

    # Wait for transaction confirmation
    receipt = w3_eth.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    if receipt.status != 1:
        raise Exception("Approve transaction failed")
    print(f"Approve confirmed in block {receipt.blockNumber}")
    return tx_hash.hex()

def deposit_to_polygon(amount_in_wei):
    """Step 2: Deposit tokens to Polygon"""
    root_chain_manager = w3_eth.eth.contract(
        address=Web3.to_checksum_address(ROOT_CHAIN_MANAGER_ADDRESS),
        abi=root_chain_manager_abi
    )

    # Build deposit transaction
    nonce = w3_eth.eth.get_transaction_count(my_address)
    txn = root_chain_manager.functions.depositFor(
        ROOT_TOKEN_ADDRESS,
        amount_in_wei
    ).build_transaction({
        "from": my_address,
        "chainId": 1,  # Ethereum mainnet
        "nonce": nonce,
    })

    # Estimate gas and set EIP-1559 fees
    gas_limit = w3_eth.eth.estimate_gas(txn)
    txn["gas"] = int(gas_limit * 1.1)

    base_fee = w3_eth.eth.get_block("latest")["baseFeePerGas"]
    priority_fee = w3_eth.eth.max_priority_fee
    max_fee = base_fee * 2 + priority_fee
    txn["maxPriorityFeePerGas"] = priority_fee
    txn["maxFeePerGas"] = max_fee

    # Sign and send transaction
    signed_txn = w3_eth.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3_eth.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Deposit TX sent: {tx_hash.hex()}")

    # Wait for transaction confirmation
    receipt = w3_eth.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    if receipt.status != 1:
        raise Exception("Deposit transaction failed")
    print(f"Deposit confirmed in block {receipt.blockNumber}")
    print("Tokens will be available on Polygon after checkpoint (15-30 minutes)")
    return tx_hash.hex()

def main():
    # Amount of tokens to bridge (example: 100 tokens with 18 decimals)
    amount = 100
    amount_in_wei = amount * (10**18)

    try:
        # Step 1: Approve tokens
        approve_token(amount_in_wei)

        # Step 2: Deposit to Polygon
        deposit_to_polygon(amount_in_wei)

        print("Bridge process initiated successfully!")
        print("Please wait for the next checkpoint (15-30 minutes) for tokens to appear on Polygon")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
