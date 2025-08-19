import React from 'react';
import { useParams } from 'react-router-dom';
import useTestWebSocket from '../../hooks/useTestWebSocket';

function GameLobbyPageSimple() {
  const { roomId } = useParams();
  const { connected, messages, sendMessage } = useTestWebSocket(roomId);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-6">Room {roomId}</h1>
        
        <div className="bg-white rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">
            Status: {connected ? '✅ Connected' : '❌ Disconnected'}
          </h2>
          
          <div className="mb-4">
            <h3 className="font-bold mb-2">Messages:</h3>
            <div className="border rounded p-3 h-64 overflow-y-auto bg-gray-50">
              {messages.map((msg, index) => (
                <div key={index} className="mb-2 p-2 bg-white rounded shadow-sm">
                  <div className="text-xs text-gray-600">{msg.type}</div>
                  <div className="text-sm">{msg.message || JSON.stringify(msg)}</div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => sendMessage({ type: 'chat', message: 'Test message' })}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Send Test Message
            </button>
            
            <button
              onClick={() => window.location.reload()}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              Refresh
            </button>
            
            <button
              onClick={() => window.history.back()}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Back
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GameLobbyPageSimple;