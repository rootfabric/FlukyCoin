import threading
import time


def handle_request(request):
    if request.get('command') == 'getinfo':
        return {'response': f'{"123"*1000000}'}
    return {'error': 'Unknown command'}

def run_server():
    server = Server(handle_request, port=5555, host='localhost')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server is shutting down...")
        server.close()

if __name__ == '__main__':
    run_server()
