import './App.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; //루트

// Url별 화면 표시

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          {/* <Route path="/" element={<Home />} />         첫 화면 */}
          {/* <Route path="/lobby" element={<About />} />   로비 화면 */}
          {/* <Route path="/keaing" element={} />           인게임 화면 */}
        </Routes>
      </Router>
    </div>
  );
}

export default App;
