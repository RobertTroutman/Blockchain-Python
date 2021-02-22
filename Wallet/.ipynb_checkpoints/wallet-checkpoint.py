import subprocess
import json
import os
from constants import *
from web3 import Web3
from bit import *
from dotenv import load_dotenv

from web3.middleware import geth_poa_middleware
from eth_account import Account

from pathlib import Path
from getpass import getpass

from bit import wif_to_key, PrivateKeyTestnet
from bit.network import NetworkAPI

load_dotenv()

mnemonic = os.getenv('Mnemonic')

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
from web3.gas_strategies.time_based import medium_gas_price_strategy
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)


def derive_wallets(Coin, Mnemonic, Numderive):
    command = f'./hd-wallet-derive.php -g --coin={Coin} --mnemonic="{Mnemonic}" --numderive={Numderive} --cols=path,address,privkey,pubkey --format=json'
    print(command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    print(output)
    p_status = p.wait()
    keys = json.loads(output)

    return keys

derive_wallets(ETH, mnemonic, 5)

coins = {ETH:derive_wallets(ETH, mnemonic, 5), BTCTEST:derive_wallets(BTCTEST, mnemonic, 5)}

def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    if coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)
    
ETH_key = priv_key_to_account(ETH, "ca01aedcc1ae01d7a16f1168e48068c39b9b18f6b0493c5bb861a6d9d48d70ed")

# Create Transaction Function
def create_tx(coin, account, recipient, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas(
            {"from": account.address, "to": recipient, "value": amount}
        )
        trx_data = {
            "to": recipient,
            "from": account.address,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address)
        }
        return trx_data

    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(recipient, amount, BTC)])
    
# Create Send Transaction Function
def send_tx(coin, account, recipient, amount):
    tx = create_tx(coin, account, recipient, amount)
    signed_tx = account.sign_transaction(tx)
    if coin == ETH:
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return result.hex()
    elif coin == BTCTEST:
        return NetworkAPI.broadcast_tx_testnet(signed_tx)
    
send_tx(ETH, ETH_key, "0x3fCeA50b1b212F55985577f01E282784D1332CEb", 2)