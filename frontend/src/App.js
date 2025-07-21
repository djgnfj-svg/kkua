import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import ProtectedRoute from './components/ProtectedRoute';
import Loading from './Pages/Loading/Loading';
import InGame from './Pages/InGame/InGame';
import Lobby from './Pages/Lobby/Lobby';
import GameLobbyPage from './Pages/GameLobbyPage/GameLobbyPage';
import GameResult from './Pages/GameResult/GameResult';
import NotFound from './Pages/NotFound/NotFound';

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <ToastProvider>
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
            <Route
              path="/gamerooms/:roomId/result"
              element={
                <ProtectedRoute>
                  <GameResult />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
          </Router>
        </ToastProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
