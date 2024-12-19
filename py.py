from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64
from solana.rpc.api import Client
import nacl.signing
from nacl.encoding import Base64Encoder
from base58 import b58decode

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.json
        wallet_address = data['wallet_address']
        signature = data['signature']
        message = data['message']
        token_mint_address = "9eF4iX4BzeKnvJ7gSw5L725jk48zJw2m66NFxHHvpump"


        if verify_wallet_ownership(wallet_address, signature, message):

            balance = check_token_holder(wallet_address, token_mint_address)
            return jsonify({
                'success': True,
                'balance': balance
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Signature verification failed'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def verify_wallet_ownership(wallet_address, signature_base64, message):
    """
    Verify that the signature was created by the wallet owner using ed25519
    """
    try:

        message_bytes = message.encode('utf-8')
        
        signature_bytes = base64.b64decode(signature_base64)
        
        public_key_bytes = b58decode(wallet_address)
        
        verify_key = nacl.signing.VerifyKey(public_key_bytes)
        
        try:
            verify_key.verify(message_bytes, signature_bytes)
            return True
        except Exception as e:
            print(f"Verification error: {e}")
            return False
            
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False

def check_token_holder(user_address, token_mint_address):
    """
    Check if the given Solana address holds the specified token and return the balance.
    """
    try:
        url = "https://api.mainnet-beta.solana.com"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                user_address,
                {"mint": token_mint_address},
                {"encoding": "jsonParsed"}
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            token_accounts = data.get("result", {}).get("value", [])
            
            total_balance = 0
            for account in token_accounts:
                parsed_info = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                balance = float(parsed_info.get("tokenAmount", {}).get("uiAmount", 0))
                total_balance += balance
                
            return total_balance
        return 0
    except Exception as e:
        print(f"Error checking token: {e}")
        return 0

if __name__ == "__main__":
    app.run(debug=True)