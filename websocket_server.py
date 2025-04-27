# websocket_server.py
import asyncio
import websockets
import json
import logging

# Configurar o registro de logs
logging.basicConfig(level=logging.INFO)

# Armazena clientes conectados
connected_clients = set()

async def handle_client(websocket):
    logging.info(f"Cliente conectado: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    try:
        async for message in websocket:
            logging.info(f"Mensagem recebida de {websocket.remote_address}: {message}")
            try:
                data = json.loads(message)
                await process_message(data, websocket)
            except json.JSONDecodeError:
                logging.error(f"JSON inválido recebido de {websocket.remote_address}: {message}")
                await websocket.send(json.dumps({"error": "Formato JSON inválido"}))
            except Exception as e:
                logging.error(f"Erro ao processar mensagem de {websocket.remote_address}: {e}")
                await websocket.send(json.dumps({"error": "Erro ao processar mensagem"}))

    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"Cliente desconectado: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError:
        logging.error(f"Conexão do cliente fechada com erro {websocket.remote_address}")
    except Exception as e:
        logging.error(f"Erro durante a conexão de {websocket.remote_address}: {e}")
    finally:
        connected_clients.discard(websocket) 

async def process_message(data, websocket):
    if "type" in data:
        if data["type"] == "broadcast" and "message" in data:
            await broadcast_message(data)
            logging.info(f"Mensagem de Broadcast enviada: {data['message']}")
        elif data["type"] == "echo" and "message" in data:
            await websocket.send(json.dumps({"response": data['message']}))
        elif data["type"] == "test":
            await websocket.send(json.dumps({"response": "Teste está OK"}))
        else:
            logging.warning(f"Tipo de mensagem desconhecido: {data}")
            await websocket.send(json.dumps({"error": "Tipo de mensagem desconhecido"}))
    else:
        logging.warning(f"Mensagem sem campo 'type': {data}")
        await websocket.send(json.dumps({"error": "Mensagem sem tipo especificado"}))

async def broadcast_message(data):
    if connected_clients:
        logging.info(f"Enviando mensagem por broadcast para {len(connected_clients)} clientes")
        tasks = [asyncio.create_task(client.send(json.dumps(data))) for client in connected_clients]
        await asyncio.gather(*tasks)
    else:
        logging.info("Nenhum cliente conectado para broadcast.")

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    logging.info("Servidor WebSocket iniciado em ws://0.0.0.0:8765")
    await asyncio.Future()  # Mantém o servidor em execução indefinidamente

if __name__ == "__main__":
    asyncio.run(main())
