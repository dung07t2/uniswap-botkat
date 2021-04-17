from web3 import Web3
import json
import time
from var import keys, contract_common_keys, contract_kat_keys

# works
web3 = Web3(Web3.HTTPProvider(keys["infura_url"]))

# uniswap contract
uniswap_contract_abi = json.loads(contract_common_keys["uniswap_abi"])
uniswap_contract_address = Web3.toChecksumAddress(contract_common_keys["uniswap_address"])
uniswap_contract = web3.eth.contract(address=uniswap_contract_address, abi=uniswap_contract_abi)

# contracts used in path, eth->weth->kat and kat->weth->eth
weth_contract_abi = json.loads(contract_common_keys["weth_abi"])
weth_contract_address = Web3.toChecksumAddress(contract_common_keys["weth_token"])
weth_contract = web3.eth.contract(address=weth_contract_address, abi=weth_contract_abi)


def read_data_from_json_file(file_name):
    with open(file_name) as json_file:
        data = json.load(json_file)
    return data


kat_contract_abi = read_data_from_json_file('kat-swap.abi.json')
kat_contract_address = Web3.toChecksumAddress(contract_kat_keys["kat_token"])
kat_contract = web3.eth.contract(address=kat_contract_address, abi=kat_contract_abi)


def get_kat_amount():
    kat_amount = kat_contract.functions.amount().call()
    return kat_amount


def convert_toWei(string: str):
    return web3.utils.toWei(string)


def sell(kat_out: int, slippage: float, receiver: str):
    amountIn = kat_out
    amountOutMin = int(kat_out * get_price_kat_to_eth() * (1 - slippage))
    path = [Web3.toChecksumAddress(contract_kat_keys["kat_token"]),
            Web3.toChecksumAddress(contract_common_keys["weth_token"])]
    to = receiver
    deadline = web3.eth.getBlock("latest")["timestamp"] + 120  # added 120 seconds from when the transaction was sent
    txn = uniswap_contract.functions.swapExactTokensForETH(amountIn=amountIn, amountOutMin=amountOutMin, path=path,
                                                           to=to, deadline=deadline).buildTransaction({
        'nonce': web3.eth.getTransactionCount(keys["my_account"]),
        'value': web3.toWei(0, 'ether'),
        'gas': keys["gas_limit"],
        'gasPrice': web3.toWei(keys["gas_price"], 'gwei')})
    signed_tx = web3.eth.account.signTransaction(txn, keys["private_key"])
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(web3.toHex(tx_hash))
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    print("sell successful")
    print("one kat is worth this much eth: " + str(get_price_kat_to_eth()))


def get_price_kat_to_eth():
    univ2_kat_balance = kat_contract.functions.balanceOf(contract_kat_keys["kat_weth_univ2_contract"]).call()
    univ2_weth_balance = weth_contract.functions.balanceOf(contract_kat_keys["kat_weth_univ2_contract"]).call()
    return univ2_weth_balance / univ2_kat_balance


def swap(amount):
    gasOption = ""
    # kat_amount = get_kat_amount()
    # hard code
    # kat_amount = 40000
    # for address in account_address:
    return kat_contract.functions.swap(amount).call()


def check_connect():
    try:
        web3.isConnected()
        print('Successful')
    except:
        raise Exception('web3 did not connect to network')


def get_balance_of(account: str):
    return kat_contract.functions.balanceOf(account).call()


def run():
    check_connect()
    for acc in keys[["my_account"]]:
        kat_balance_of = get_balance_of(acc)
        try:
            swap(kat_balance_of)
            print('success')
        except:
            print('Swap error at' + acc)

    # Uncomment below line if the swap func did not found. We will imagine a swap like a sell to coin
    # sell(kat_contract.functions.balanceOf(keys["my_account"]).call(), keys["slippage"], keys["my_account"])


run()
