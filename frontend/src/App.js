import './App.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; //루트
import Loading from './Pages/Loading/Loading';
import InGame from './InGame/InGame';
import Lobby from './Pages/Lobby/Lobby';
import GameLobbyPage from './Pages/GameLobbyPage/GameLobbyPage';


// Url별 화면 표시

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/" element={<Loading />} />
          <Route path="/keaing" element={<InGame />} />
          <Route path="/lobby" element={<Lobby />} />
          <Route path="/lobby/keaLobby/:lobbyid" element={<GameLobbyPage />} />  
        </Routes>
      </Router>
    </div>
  );
}

export default App;
