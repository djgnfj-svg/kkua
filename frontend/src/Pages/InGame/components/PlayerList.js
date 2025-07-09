import React from 'react';

const PlayerList = ({ players, specialPlayer }) => {
  return (
    <div className="flex flex-wrap justify-center gap-4 mb-8">
      {players.map((player, index) => (
        <div
          key={index}
          className={`bg-white p-4 rounded shadow ${
            player === specialPlayer ? 'border-2 border-blue-500' : ''
          }`}
        >
          {player}
        </div>
      ))}
    </div>
  );
};

export default PlayerList;
