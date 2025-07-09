import './App.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Loading from './Pages/Loading/Loading';
import InGame from './Pages/InGame/InGame';
import Lobby from './Pages/Lobby/Lobby';
import GameLobbyPage from './Pages/GameLobbyPage/GameLobbyPage';

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Loading />} />
            <Route
              path="/lobby"
              element={
                <ProtectedRoute>
                  <Lobby />
                </ProtectedRoute>
              }
            />
            <Route
              path="/kealobby/:roomId"
              element={
                <ProtectedRoute>
                  <GameLobbyPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/keaing/:gameid"
              element={
                <ProtectedRoute>
                  <InGame />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Router>
      </AuthProvider>
    </div>
  );
}

export default App;
