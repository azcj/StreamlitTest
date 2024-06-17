# from Jaron

from web3 import Web3
import json
import streamlit as st
import pandas as pd
import numpy as np


# setup w3:
rpc_url = 'https://real.drpc.org'
w3 = Web3(Web3.HTTPProvider(rpc_url))


# constants:
Q96 = 2 ** 96


# ABIs:
abi_file = 'ABIs/PearlV2Pool.abi'
with open(abi_file) as json_data:
    pool_abi = json.load(json_data)
abi_file = 'ABIs/NonfungiblePositionManager.abi'
with open(abi_file) as json_data:
    nfpm_abi = json.load(json_data)
abi_file = 'ABIs/PearlV2Factory.abi'
with open(abi_file) as json_data:
    pool_factory_abi = json.load(json_data)
abi_file = 'ABIs/RWAToken.abi'
with open(abi_file) as json_data:
    erc20_abi = json.load(json_data)


# contracts:
nfpm = '0x153e99930da597EA11144327afC6Ae5E6f853575'
nfpm_contract = w3.eth.contract(nfpm, abi=nfpm_abi) # access the smart contract
pool_factory = '0xeF0b0a33815146b599A8D4d3215B18447F2A8101'
pool_factory_contract = w3.eth.contract(pool_factory, abi=pool_factory_abi)


# some Uni V3 functions:
def get_liq_for_amount0(p1, p2, amount0):
    return amount0 * (p1 * p2 / Q96) / (p2 - p1)


def get_liq_for_amount1(p1, p2, amount1):
    return amount1 * Q96 / (p2 - p1)


def get_liq_for_amounts(p, p1, p2, amount0, amount1):
    if p <= p1:
        L = get_liq_for_amount0(p1, p2, amount0)
    elif p < p2:
        L0 = get_liq_for_amount0(p, p2, amount0)
        L1 = get_liq_for_amount1(p1, p, amount1)
        L = min(L0, L1)
    else:
        L = get_liq_for_amount1(p1, p2, amount1)
    return L

def get_amount0_delta(p1, p2, L):
    return L * Q96 * (p2 - p1) / p2 / p1


def get_amount1_delta(p1, p2, L):
    return L * (p2 - p1) / Q96


def get_amount_deltas(L, p, p1, p2):
    if p < p1:
        amount0 = get_amount0_delta(p1, p2, L)
        amount1 = 0
    elif p < p2:
        amount0 = get_amount0_delta(p, p2, L)
        amount1 = get_amount1_delta(p1, p, L)
    else:
        amount0 = 0
        amount1 = get_amount1_delta(p1, p2, L)
    return amount0, amount1


# streamlit (my edits)
st.title('Dashboard title')

token_id = st.number_input("Please enter a token ID",
        value = 207,
        key="placeholder")

# grab position data:
position_data = nfpm_contract.functions.positions(token_id).call()
token0 = position_data[2]
token1 = position_data[3]
fee = position_data[4]
tick1 = position_data[5]
tick2 = position_data[6]
liquidity = position_data[7]

# get current price and range:
pool = pool_factory_contract.functions.getPool(token0, token1, fee).call()
pool_contract = w3.eth.contract(pool, abi=pool_abi)
slot0_data = pool_contract.functions.slot0().call()
price = slot0_data[0]
p1 = int(1.0001 ** (tick1 / 2) * Q96)
p2 = int(1.0001 ** (tick2 / 2) * Q96)

# tokens:
token0_contract = w3.eth.contract(token0, abi=erc20_abi)
token0_symbol = token0_contract.functions.symbol().call()
token0_decimals = token0_contract.functions.decimals().call()
token1_contract = w3.eth.contract(token1, abi=erc20_abi)
token1_symbol = token1_contract.functions.symbol().call()
token1_decimals = token1_contract.functions.decimals().call()

# get balances:
amount0, amount1 = get_amount_deltas(liquidity, price, p1, p2)
st.text(f'{amount0 / 10 ** token0_decimals} {token0_symbol}, {amount1 / 10 ** token1_decimals} {token1_symbol} still in NFT')
