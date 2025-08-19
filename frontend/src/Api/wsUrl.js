/* 웹 소켓 api 주소 */
const WS_BASE_URL =
  process.env.REACT_APP_WS_BASE_URL ||
  process.env.REACT_APP_WS_URL ||
  'ws://localhost:8000';

export const LOBBY_SOCKET_URL = `${WS_BASE_URL}/ws/lobby/`;
